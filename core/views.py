import base64
import binascii
import json
import secrets

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from django.contrib import messages

from django.contrib.auth import login as auth_login, logout, update_session_auth_hash

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import identify_hasher, make_password

from django.contrib.auth.models import User

from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import RequestDataTooBig
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Max, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse, reverse_lazy

from django.utils import timezone
from django.utils.dateparse import parse_date

from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_GET, require_POST

from django.conf import settings

from PIL import Image, ImageOps

from .forms import ApiConfigurationForm, BotSubscriptionChannelForm, EmployeeProfileForm, ExternalApiConnectionForm, IntakeRequestForm, LoginForm, PlatformForm, PositionForm, SiteIntakeForm, SiteSettingsForm, StationForm, StyledPasswordChangeForm, UserForm, UserInfoForm, UserProfileForm, WebPlatformForm
from .excel_utils import build_xlsx, parse_xlsx, truthy
from .hrm_client import HRMClient, NOT_FOUND_MESSAGE
from .models import AdminChatMessage, AdminChatThread, ApiConfiguration, BotSubscriptionChannel, ExternalApiConnection, IntakeRequest, InternalChat, InternalChatMessage, InternalChatParticipant, InternalContact, Platform, Position, SiteLog, SiteSettings, Station, UserProfile, WebPlatform, WebPlatformFavorite
from .site_logs import write_site_log
from .telegram import get_telegram_profile_photo, send_telegram_media, send_telegram_message
from .utils import generate_login, generate_password, mask_value, user_can_administer, user_can_manage


def _is_django_password_hash(value):
    if not value:
        return False
    try:
        identify_hasher(value)
    except ValueError:
        return False
    return True


def _request_password_cache(request):
    cache = request.session.setdefault("intake_plain_passwords", {})
    if not isinstance(cache, dict):
        cache = {}
        request.session["intake_plain_passwords"] = cache
    return cache


def _store_plain_request_password(request, item_id, password):
    cache = _request_password_cache(request)
    cache[str(item_id)] = password
    request.session.modified = True


def _get_plain_request_password(request, item):
    cache = _request_password_cache(request)
    password = cache.get(str(item.pk))
    if password:
        return password
    if item.generated_password and not _is_django_password_hash(item.generated_password):
        return item.generated_password
    return ""


def _url_language(request):
    code = (request.path.strip("/").split("/") or ["ru"])[0] or "ru"
    return code if code in {"ru", "uz", "uz-cyrl", "en"} else getattr(request, "LANGUAGE_CODE", "ru")





class LoginView(DjangoLoginView):

    authentication_form = LoginForm

    template_name = "login.html"

    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["web_platforms"] = WebPlatform.objects.filter(is_active=True).order_by("sort_order", "name")
        return context



# RU: Блок OneID/E-IMZO ниже отвечает за внешний вход через государственный SSO.
# UZ: Quyidagi OneID/E-IMZO bloki davlat SSO orqali tashqi kirishni boshqaradi.
# EN: The OneID/E-IMZO block below handles external login through the government SSO.
def index(request):
    lang_code = _url_language(request)
    form = SiteIntakeForm(request.POST or None, lang_code=lang_code)

    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            try:
                hrm = HRMClient().find_employee(data["pnfl"], data["phone"])
            except Exception as exc:
                hrm = {"found": False, "message": NOT_FOUND_MESSAGE, "raw": {"error": str(exc)}}
                write_site_log(
                    request,
                    level=SiteLog.Level.ERROR,
                    source="hrm",
                    action="site_intake_check_worker",
                    message=str(exc),
                    status_code=502,
                    meta={"pnfl": data["pnfl"], "phone": data["phone"]},
                )

            if hrm.get("found"):
                item = IntakeRequest.objects.create(
                    platform=data["platform"],
                    cause=data["cause"],
                    pnfl=data["pnfl"],
                    company=data["company"],
                    position=data["position"],
                    full_name=data["full_name"],
                    passport=data["passport"],
                    phone=hrm.get("phone") or data["phone"],
                    telegram_id=0,
                    lang=lang_code,
                    hrm_payload={"found": True, "message": hrm.get("message", ""), "raw": hrm.get("raw", {})},
                )
                write_site_log(
                    request,
                    source="site",
                    action="site_intake_create",
                    message=f"Created site intake request #{item.id}",
                    meta={"request_id": item.id, "pnfl": data["pnfl"], "platform": data["platform"]},
                )
                messages.success(request, form.texts["success"])
                return redirect("index")

            message = hrm.get("message") or form.texts["not_found"]
            messages.error(request, message)

    web_platforms = WebPlatform.objects.filter(is_active=True).order_by("sort_order", "name")
    return render(request, "index.html", {"form": form, "web_platforms": web_platforms})


def _merge_query(url, params):
    # RU: Аккуратно добавляет параметры к URL, не ломая уже существующую query string.
    # UZ: URL ichidagi mavjud query string buzilmasdan yangi parametrlar qo'shiladi.
    # EN: Safely appends parameters to a URL without breaking an existing query string.
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value not in (None, "")})
    return urlunparse(parsed._replace(query=urlencode(query)))


def _unique_username(base):
    # RU: Создаёт свободный username, если OneID user_id уже занят в локальной базе.
    # UZ: OneID user_id lokal bazada band bo'lsa, bo'sh username yaratadi.
    # EN: Builds an available username when the OneID user_id already exists locally.
    username = (base or "oneid-user").strip().lower().replace(" ", ".")[:140].strip(".") or "oneid-user"
    candidate = username
    counter = 1
    while User.objects.filter(username=candidate).exists():
        suffix = f".{counter}"
        candidate = f"{username[:150 - len(suffix)]}{suffix}"
        counter += 1
    return candidate


def _jwt_payload(token):
    # RU: Поддержка JWT оставлена на случай, если OneID или другой SSO вернёт id_token.
    # UZ: OneID yoki boshqa SSO id_token qaytarsa, JWT payload o'qilishi uchun qoldirilgan.
    # EN: JWT support is kept in case OneID or another SSO returns an id_token.
    parts = str(token or "").split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return {}


def _oneid_value(data, *keys):
    # RU: OneID может вернуть одно и то же поле под разными именами, поэтому ищем несколько вариантов.
    # UZ: OneID bir xil qiymatni turli nomlarda qaytarishi mumkin, shuning uchun bir nechta kalit tekshiriladi.
    # EN: OneID can return the same value under different keys, so we check several aliases.
    for item in _walk_dicts(data):
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return str(value).strip()
    return ""


def _oneid_safe_payload(value):
    # RU: Сохраняем диагностический payload без токенов, секретов, паролей и временных code.
    # UZ: Diagnostika payload token, secret, parol va vaqtinchalik code qiymatlarisiz saqlanadi.
    # EN: Store diagnostic payload without tokens, secrets, passwords, or temporary codes.
    hidden = ("token", "secret", "password", "code")
    if isinstance(value, dict):
        return {
            key: _oneid_safe_payload(item)
            for key, item in value.items()
            if not any(marker in str(key).lower() for marker in hidden)
        }
    if isinstance(value, list):
        return [_oneid_safe_payload(item) for item in value]
    return value


def _oneid_names(data):
    # RU: Нормализуем ФИО из официальных OneID полей: first_name, sur_name, mid_name, full_name.
    # UZ: F.I.O. OneID rasmiy maydonlaridan normal holatga keltiriladi: first_name, sur_name, mid_name.
    # EN: Normalize full name data from official OneID fields: first_name, sur_name, mid_name, full_name.
    first_name = _oneid_value(data, "first_name", "firstname", "given_name", "name_latin")
    last_name = _oneid_value(data, "last_name", "lastname", "surname", "sur_name", "family_name", "surname_latin")
    middle_name = _oneid_value(data, "middle_name", "patronymic", "father_name", "mid_name", "middle_name_latin")
    full_name = _oneid_value(data, "full_name", "fullName", "fio", "name")
    if full_name and not (first_name or last_name):
        last_name, first_name, middle_name = _split_hrm_full_name(full_name)
    return first_name, last_name, middle_name, full_name


def _oneid_find_user(data):
    # RU: Главный ключ сопоставления - ПНФЛ/ЖШИР (pin), затем логин OneID/user_id и email.
    # UZ: Asosiy bog'lash kaliti JSHSHIR/PINFL (pin), keyin OneID login/user_id va email.
    # EN: Primary matching key is PINFL/JSHSHIR (pin), then OneID login/user_id and email.
    pinfl = _oneid_value(data, "pinfl", "pnfl", "pin", "jshshir", "personal_number")
    if pinfl:
        user = (
            User.objects.filter(Q(profile__pnfl=pinfl) | Q(profile__employee_pinfl=pinfl), is_active=True)
            .select_related("profile")
            .first()
        )
        if user:
            return user

    for key in ("username", "login", "user_login", "preferred_username", "user_id", "sub"):
        username = _oneid_value(data, key)
        if username:
            user = User.objects.filter(username=username, is_active=True).first()
            if user:
                return user

    email = _oneid_value(data, "email", "mail")
    if email:
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            return user
    return None


def _oneid_apply_profile(user, data):
    # RU: После успешного входа обновляем профиль сайта данными OneID, чтобы HRM/Face ID видели актуальные поля.
    # UZ: Muvaffaqiyatli kirishdan keyin sayt profili OneID ma'lumotlari bilan yangilanadi.
    # EN: After a successful login, update the local profile with OneID data for HRM/Face ID consistency.
    first_name, last_name, middle_name, full_name = _oneid_names(data)
    email = _oneid_value(data, "email", "mail")
    changed_fields = []
    if first_name and user.first_name != first_name:
        user.first_name = first_name
        changed_fields.append("first_name")
    if last_name and user.last_name != last_name:
        user.last_name = last_name
        changed_fields.append("last_name")
    if email and user.email != email:
        user.email = email
        changed_fields.append("email")
    if changed_fields:
        user.save(update_fields=changed_fields)

    profile = _ensure_user_profile(user)
    pinfl = _oneid_value(data, "pinfl", "pnfl", "pin", "jshshir", "personal_number")
    if pinfl:
        profile.pnfl = pinfl
        profile.employee_pinfl = pinfl
    if middle_name:
        profile.middle_name = middle_name
    phone = _oneid_value(data, "phone", "phone_number", "mobile_phone", "mob_phone")
    if phone:
        profile.phone = phone
    birth = _oneid_value(data, "birth_date", "birthDate", "date_of_birth")
    if birth:
        profile.birth_date = _profile_birth_date(birth)
    passport = _oneid_value(data, "pport_no", "passport", "passport_no")
    legal_tin = _oneid_value(data, "pkcs_legal_tin", "legal_tin")
    if full_name and not (profile.middle_name or user.first_name or user.last_name):
        last_name, first_name, middle_name = _split_hrm_full_name(full_name)
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])
        profile.middle_name = middle_name
    profile.hrm_payload = {
        "oneid": _oneid_safe_payload(data),
        "oneid_passport": passport,
        "oneid_legal_tin": legal_tin,
        "oneid_auth_method": _oneid_value(data, "auth_method"),
    }
    profile.hrm_synced_at = timezone.now()
    profile.save()
    return profile


def _oneid_create_user(config, data):
    # RU: Если включено автосоздание, пользователь OneID получает локальный аккаунт без пароля.
    # UZ: Avtomatik yaratish yoqilgan bo'lsa, OneID foydalanuvchisi parolsiz lokal akkaunt oladi.
    # EN: When auto-create is enabled, the OneID user gets a local account with an unusable password.
    if not config.oneid_auto_create_user:
        return None
    first_name, last_name, middle_name, full_name = _oneid_names(data)
    pinfl = _oneid_value(data, "pinfl", "pnfl", "pin", "jshshir", "personal_number")
    username = _oneid_value(data, "username", "login", "preferred_username", "user_id")
    username = username or generate_login(full_name or f"{last_name} {first_name}", pinfl)
    user = User.objects.create_user(
        username=_unique_username(username),
        email=_oneid_value(data, "email", "mail"),
        first_name=first_name,
        last_name=last_name,
    )
    user.set_unusable_password()
    user.save()
    profile = _ensure_user_profile(user)
    profile.middle_name = middle_name
    profile.save(update_fields=["middle_name", "updated_at"])
    _oneid_apply_profile(user, data)
    return user


def _oneid_callback_url(request):
    # RU: Callback строится динамически, чтобы учитывать текущий язык: /ru/, /uz/, /en/.
    # UZ: Callback joriy til prefiksini hisobga olib dinamik yaratiladi: /ru/, /uz/, /en/.
    # EN: Callback is generated dynamically to include the active language prefix: /ru/, /uz/, /en/.
    return request.build_absolute_uri(reverse("oneid_callback"))


def _oneid_start(request, *, method):
    # RU: Старт SSO: генерируем state, сохраняем next и отправляем пользователя в OneID.
    # UZ: SSO boshlanishi: state yaratiladi, next saqlanadi va foydalanuvchi OneIDga yuboriladi.
    # EN: SSO start: generate state, store next URL, and redirect the user to OneID.
    config = ApiConfiguration.load()
    if not config.oneid_enabled:
        messages.error(request, "OneID не включен в настройках API.")
        return redirect("login")
    if method != "IDPW" and not config.eimzo_enabled:
        messages.error(request, "E-IMZO вход не включен в настройках API.")
        return redirect("login")
    if not config.oneid_client_id or not config.oneid_client_secret or not config.oneid_scope or not config.oneid_authorize_url:
        messages.error(request, "Заполните OneID client_id, client_secret, scope и Authorization URL в настройках API.")
        return redirect("login")

    state = secrets.token_urlsafe(24)
    request.session["oneid_state"] = state
    request.session["oneid_next"] = request.GET.get("next") or reverse("dashboard")
    request.session["oneid_method"] = method
    auth_url = _merge_query(
        config.oneid_authorize_url,
        {
            # RU: У OneID Узбекистана используется response_type=one_code, не стандартный OAuth code.
            # UZ: O'zbekiston OneID tizimida oddiy OAuth code emas, response_type=one_code ishlatiladi.
            # EN: Uzbekistan OneID uses response_type=one_code, not the standard OAuth code value.
            "client_id": config.oneid_client_id,
            "response_type": "one_code",
            "redirect_uri": _oneid_callback_url(request),
            "scope": config.oneid_scope,
            "state": state,
            "method": method,
        },
    )
    return redirect(auth_url)


def oneid_login_start(request):
    # RU: Обычный вход OneID через логин/пароль.
    # UZ: OneID oddiy login/parol orqali kirish.
    # EN: Standard OneID login through username/password.
    return _oneid_start(request, method="IDPW")


def eimzo_login_start(request):
    # RU: Вход через E-IMZO использует тот же OneID flow, но с отдельным method.
    # UZ: E-IMZO kirishi ham shu OneID flowdan foydalanadi, faqat method alohida.
    # EN: E-IMZO login uses the same OneID flow with a separate method value.
    config = ApiConfiguration.load()
    return _oneid_start(request, method=(config.eimzo_oneid_method or "EIMZO"))


def _oneid_token_data(config, code, redirect_uri):
    # RU: Меняем code на access_token через официальный OneID grant_type=one_authorization_code.
    # UZ: code rasmiy OneID grant_type=one_authorization_code orqali access_tokenga almashtiriladi.
    # EN: Exchange code for access_token through the official OneID grant_type=one_authorization_code.
    token_url = config.oneid_token_url or config.oneid_authorize_url
    if not token_url:
        raise ValueError("OneID token URL is not configured.")
    response = requests.post(
        token_url,
        data={
            "grant_type": "one_authorization_code",
            "client_id": config.oneid_client_id,
            "client_secret": config.oneid_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": config.oneid_scope,
        },
        headers={"Accept": "application/json"},
        timeout=20,
        verify=config.oneid_verify_ssl,
    )
    response.raise_for_status()
    return response.json()


def _oneid_userinfo(config, token_data):
    # RU: После получения access_token отдельно запрашиваем данные пользователя через one_access_token_identify.
    # UZ: access_token olingach, foydalanuvchi ma'lumotlari one_access_token_identify orqali so'raladi.
    # EN: After receiving access_token, fetch user data separately via one_access_token_identify.
    result = dict(token_data or {})
    id_payload = _jwt_payload(token_data.get("id_token"))
    if id_payload:
        result["id_token_payload"] = id_payload
    access_token = token_data.get("access_token") or token_data.get("token")
    userinfo_url = config.oneid_userinfo_url or config.oneid_token_url or config.oneid_authorize_url
    if userinfo_url and access_token:
        response = requests.post(
            userinfo_url,
            data={
                "grant_type": "one_access_token_identify",
                "client_id": config.oneid_client_id,
                "client_secret": config.oneid_client_secret,
                "access_token": access_token,
                "scope": config.oneid_scope,
            },
            headers={"Accept": "application/json"},
            timeout=20,
            verify=config.oneid_verify_ssl,
        )
        response.raise_for_status()
        result["userinfo"] = response.json()
    return result


def oneid_callback(request):
    # RU: Callback принимает ответ OneID, проверяет state, получает профиль и логинит пользователя в Django.
    # UZ: Callback OneID javobini qabul qiladi, state tekshiradi, profilni oladi va Django ichida login qiladi.
    # EN: Callback receives OneID response, verifies state, loads profile data, and logs the user into Django.
    config = ApiConfiguration.load()
    expected_state = request.session.pop("oneid_state", "")
    received_state = request.GET.get("state", "")
    if not expected_state or not received_state or received_state != expected_state:
        messages.error(request, "OneID state не совпал. Повторите вход.")
        return redirect("login")
    if request.GET.get("error"):
        messages.error(request, request.GET.get("error_description") or request.GET.get("error"))
        return redirect("login")

    code = request.GET.get("code")
    if request.GET.get("access_token"):
        token_data = {"access_token": request.GET.get("access_token")}
    elif code:
        try:
            token_data = _oneid_token_data(config, code, _oneid_callback_url(request))
        except Exception as exc:
            write_site_log(request, level=SiteLog.Level.ERROR, source="oneid", action="token", message=str(exc), status_code=502)
            messages.error(request, f"OneID token error: {exc}")
            return redirect("login")
    else:
        messages.error(request, "OneID не вернул code/access_token.")
        return redirect("login")

    try:
        oneid_data = _oneid_userinfo(config, token_data)
    except Exception as exc:
        write_site_log(request, level=SiteLog.Level.ERROR, source="oneid", action="userinfo", message=str(exc), status_code=502)
        messages.error(request, f"OneID userinfo error: {exc}")
        return redirect("login")

    user = _oneid_find_user(oneid_data) or _oneid_create_user(config, oneid_data)
    if not user:
        messages.error(request, "Пользователь OneID не найден. Включите автосоздание или привяжите ПНФЛ/ЖШИР.")
        return redirect("login")

    _oneid_apply_profile(user, oneid_data)
    auth_login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
    write_site_log(request, source="oneid", action="login", message=f"OneID login: {user.username}")
    return redirect(request.session.pop("oneid_next", reverse("dashboard")))



def _normalized_face_image(source):
    image = Image.open(source)
    image = ImageOps.exif_transpose(image).convert("L")
    width, height = image.size
    side = min(width, height)
    left = max((width - side) // 2, 0)
    top = max((height - side) // 2, 0)
    image = image.crop((left, top, left + side, top + side))
    return ImageOps.equalize(image)


def _average_hash(image, size=16):
    sample = image.resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(sample.getdata())
    average = sum(pixels) / len(pixels)
    return tuple(pixel >= average for pixel in pixels)


def _difference_hash(image, width=17, height=16):
    sample = image.resize((width, height), Image.Resampling.LANCZOS)
    pixels = list(sample.getdata())
    bits = []
    for row in range(height):
        offset = row * width
        for col in range(width - 1):
            bits.append(pixels[offset + col] > pixels[offset + col + 1])
    return tuple(bits)


def _hash_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return 0
    distance = sum(a != b for a, b in zip(left, right))
    return 1 - (distance / len(left))


def _face_similarity(uploaded_image, profile_image):
    candidate = _normalized_face_image(uploaded_image)
    reference = _normalized_face_image(profile_image)
    average_score = _hash_similarity(_average_hash(candidate), _average_hash(reference))
    shape_score = _hash_similarity(_difference_hash(candidate), _difference_hash(reference))
    return max(average_score, shape_score)


FACE_MATCH_THRESHOLD = 0.62
FACE_AUTO_MATCH_THRESHOLD = 0.66


def _face_api_connections():
    markers = ("face", "faceid", "face_id", "face-login", "biometric", "biometr", "yuz")
    marker_query = Q()
    for marker in markers:
        marker_query |= Q(name__icontains=marker) | Q(base_url__icontains=marker) | Q(notes__icontains=marker)
    return list(
        ExternalApiConnection.objects.filter(is_active=True)
        .filter(Q(purpose=ExternalApiConnection.Purpose.FACE_ID) | marker_query)
    )


def _external_api_timeout(connection):
    timeout = connection.timeout_seconds or 15
    return max(1, min(timeout, 120))


def _remember_external_api_check(connection, *, status_code=None, error=""):
    connection.last_status_code = status_code
    connection.last_checked_at = timezone.now()
    connection.last_error = (error or "")[:1000]
    connection.save(update_fields=["last_status_code", "last_checked_at", "last_error", "updated_at"])


def _face_api_verified(data):
    if not isinstance(data, dict):
        return False
    if data.get("ok") is False or data.get("success") is False or data.get("error") is True:
        return False
    if data.get("matched") is True or data.get("verified") is True or data.get("found") is True or data.get("ok") is True:
        return True
    return data.get("success") is True


def _face_api_success(data):
    if _face_api_verified(data):
        return True
    if not isinstance(data, dict):
        return False
    if data.get("ok") is False or data.get("success") is False or data.get("error") is True:
        return False
    return any(isinstance(data.get(key), dict) for key in ("user", "employee", "data", "result"))


def _walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)


def _clean_identifier(value):
    return str(value or "").strip()


def _user_from_face_api_data(data, requested_username=""):
    if requested_username and _face_api_verified(data):
        return User.objects.filter(username=requested_username, is_active=True).first()

    for item in _walk_dicts(data):
        for key in ("username", "login", "user_login", "account", "account_login"):
            value = _clean_identifier(item.get(key))
            if value:
                user = User.objects.filter(username=value, is_active=True).first()
                if user:
                    return user

        email = _clean_identifier(item.get("email"))
        if email:
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if user:
                return user

        user_id = _clean_identifier(item.get("user_id") or item.get("django_user_id"))
        if user_id.isdigit():
            user = User.objects.filter(pk=int(user_id), is_active=True).first()
            if user:
                return user

        for key in ("pnfl", "pin", "pinfl"):
            value = _clean_identifier(item.get(key))
            if value:
                request_item = IntakeRequest.objects.filter(
                    Q(pnfl=value) | Q(generated_login=value),
                    django_user__isnull=False,
                    django_user__is_active=True,
                ).select_related("django_user").order_by("-created_at").first()
                if request_item:
                    return request_item.django_user
    return None


def _try_face_api_login(image_data, username=""):
    connections = _face_api_connections()
    if not connections:
        return None, "face_api_not_configured"

    image_base64 = image_data.split(",", 1)[1] if "," in image_data else image_data
    payload = {
        "image": image_data,
        "image_base64": image_base64,
        "username": username,
        "login": username,
    }

    last_error = "face_api_error"
    for connection in connections:
        if not connection.base_url:
            continue
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if connection.api_key:
            headers[connection.auth_header or "X-API-KEY"] = connection.api_key
        response = None
        try:
            response = requests.post(connection.base_url, json=payload, headers=headers, timeout=_external_api_timeout(connection))
            _remember_external_api_check(connection, status_code=response.status_code)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            last_error = "face_api_error"
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code is None and response is not None:
                status_code = response.status_code
            _remember_external_api_check(connection, status_code=status_code, error=str(exc))
            write_site_log(
                None,
                level=SiteLog.Level.ERROR,
                source="face_id",
                action="external_face_api",
                message=f"{connection.name}: {exc}",
                status_code=502,
            )
            continue

        user = _user_from_face_api_data(data, requested_username=username)
        if user:
            return user, ""
        if _face_api_success(data):
            last_error = "face_user_not_found"
    return None, last_error


def _test_external_api_connection(connection):
    url = connection.test_url
    if not url:
        raise ValueError("Base URL or health-check URL is required.")

    headers = {"Accept": "application/json"}
    if connection.api_key:
        headers[connection.auth_header or "X-API-KEY"] = connection.api_key

    timeout = _external_api_timeout(connection)
    if connection.method == ExternalApiConnection.Method.GET:
        response = requests.get(url, headers=headers, timeout=timeout)
    else:
        headers["Content-Type"] = "application/json"
        response = requests.post(url, json={"ping": True, "source": "mtu_forum"}, headers=headers, timeout=timeout)

    error = "" if response.status_code < 400 else response.text[:500]
    _remember_external_api_check(connection, status_code=response.status_code, error=error)
    return response


def _image_from_data_url(value):
    if not value or "," not in value:
        raise ValueError("empty_image")
    _, encoded = value.split(",", 1)
    try:
        return BytesIO(base64.b64decode(encoded, validate=True))
    except (binascii.Error, ValueError) as exc:
        raise ValueError("bad_image") from exc


def _ensure_profile_avatar_for_face(profile):
    if profile.avatar:
        return True
    if profile.hrm_photo and _save_hrm_profile_photo(profile, profile.hrm_photo, replace=False):
        profile.save(update_fields=["avatar", "hrm_photo", "updated_at"])
        return True
    return False


def _local_face_login_user(image_data, username=""):
    uploaded_image = _image_from_data_url(image_data)
    uploaded_bytes = uploaded_image.getvalue()

    profiles = UserProfile.objects.select_related("user").filter(user__is_active=True)
    if username:
        if not User.objects.filter(username=username, is_active=True).exists():
            return None, "user_not_found", 0
        profiles = profiles.filter(user__username=username)

    best_user = None
    best_score = 0
    checked = 0
    for profile in profiles:
        if not _ensure_profile_avatar_for_face(profile):
            continue
        try:
            with profile.avatar.open("rb") as reference:
                similarity = _face_similarity(BytesIO(uploaded_bytes), reference)
        except (OSError, ValueError):
            continue
        checked += 1
        if similarity > best_score:
            best_score = similarity
            best_user = profile.user

    if not checked:
        return None, "face_not_configured", 0

    threshold = FACE_MATCH_THRESHOLD if username else FACE_AUTO_MATCH_THRESHOLD
    if best_user and best_score >= threshold:
        return best_user, "", best_score
    return None, "face_not_matched", best_score


@require_POST
def face_login_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (RequestDataTooBig, UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "message": "bad_request"}, status=400)

    username = (payload.get("username") or "").strip()
    image_data = payload.get("image") or ""
    if not image_data:
        return JsonResponse({"ok": False, "message": "face_read_error"}, status=400)

    api_user, api_error = _try_face_api_login(image_data, username=username)
    if api_user:
        api_user.backend = settings.AUTHENTICATION_BACKENDS[0]
        auth_login(request, api_user)
        return JsonResponse({"ok": True, "redirect": reverse("dashboard"), "source": "api"})

    try:
        local_user, local_error, similarity = _local_face_login_user(image_data, username=username)
    except (OSError, ValueError):
        return JsonResponse({"ok": False, "message": "face_read_error"}, status=400)

    if not local_user:
        status = 404 if username and local_error in {"face_not_configured", "user_not_found"} else 403
        return JsonResponse({"ok": False, "message": local_error or api_error or "face_not_matched", "score": round(similarity, 3)}, status=status)

    local_user.backend = settings.AUTHENTICATION_BACKENDS[0]
    auth_login(request, local_user)
    return JsonResponse({"ok": True, "redirect": reverse("dashboard"), "score": round(similarity, 3), "source": "local"})





@login_required

def logout_view(request):

    logout(request)

    return redirect("login")





@login_required

def dashboard(request):

    can_manage = user_can_manage(request.user)
    deleted_by_platform = defaultdict(int)
    platform_stats = []
    if can_manage:
        for meta in SiteLog.objects.filter(action="request_delete").values_list("meta", flat=True):
            if isinstance(meta, dict):
                deleted_by_platform[meta.get("platform") or ""] += 1

        platform_counts = defaultdict(lambda: {"total": 0, "done": 0, "blocked": 0})
        for row in IntakeRequest.objects.values("platform", "status").annotate(total=Count("id")):
            platform_name = row["platform"] or ""
            platform_counts[platform_name]["total"] += row["total"]
            if row["status"] == IntakeRequest.Status.DONE:
                platform_counts[platform_name]["done"] += row["total"]
            elif row["status"] == IntakeRequest.Status.BLOCKED:
                platform_counts[platform_name]["blocked"] += row["total"]

        for platform in Platform.objects.filter(is_active=True):
            aliases = [platform.name]
            if platform.code and platform.code != platform.name:
                aliases.append(platform.code)

            platform_stats.append({
                "name": platform.name,
                "total": sum(platform_counts[alias]["total"] for alias in aliases),
                "done": sum(platform_counts[alias]["done"] for alias in aliases),
                "blocked_unblocked": sum(platform_counts[alias]["blocked"] for alias in aliases),
                "deleted": sum(deleted_by_platform[alias] for alias in aliases),
            })

    stats = {

        "new": IntakeRequest.objects.filter(status=IntakeRequest.Status.NEW).count() if can_manage else 0,

        "done": IntakeRequest.objects.filter(status=IntakeRequest.Status.DONE).count() if can_manage else 0,

        "blocked": IntakeRequest.objects.filter(status=IntakeRequest.Status.BLOCKED).count() if can_manage else 0,

        "chats": AdminChatMessage.objects.filter(direction=AdminChatMessage.Direction.IN, is_read=False).count() if can_manage else 0,

    }

    favorite_platform_ids = set(WebPlatformFavorite.objects.filter(user=request.user).values_list("platform_id", flat=True))
    web_platforms = [
        {
            "id": item.id,
            "name": item.name,
            "url": item.url,
            "open_url": reverse_lazy("open_web_platform", kwargs={"pk": item.pk}),
            "image_url": item.image_url or _favicon_url(item.url),
            "is_active": item.is_active,
            "is_favorite": item.id in favorite_platform_ids,
            "favorite_count": item.favorite_count,
            "uses": _compact_count(item.usage_count),
        }
        for item in WebPlatform.objects.annotate(favorite_count=Count("favorites"))
    ]

    return render(request, "dashboard.html", {"stats": stats, "platform_stats": platform_stats, "web_platforms": web_platforms, "show_admin_dashboard": can_manage})


@login_required
@require_POST
def toggle_web_platform_favorite(request, pk):
    platform = get_object_or_404(WebPlatform, pk=pk)
    favorite = WebPlatformFavorite.objects.filter(user=request.user, platform=platform).first()
    if favorite:
        favorite.delete()
    else:
        WebPlatformFavorite.objects.create(user=request.user, platform=platform)
    return redirect(request.POST.get("next") or "dashboard")


@login_required
def open_web_platform(request, pk):
    platform = get_object_or_404(WebPlatform, pk=pk, is_active=True)
    if not platform.url:
        return redirect("dashboard")
    WebPlatform.objects.filter(pk=platform.pk).update(usage_count=F("usage_count") + 1)
    return redirect(platform.url)




@login_required

@user_passes_test(user_can_manage)

def requests_view(request):

    return render(request, "requests.html", {"statuses": IntakeRequest.Status.choices})





@login_required

@user_passes_test(user_can_manage)

@require_GET

def dashboard_requests_api(request):

    query = request.GET.get("q", "").strip()

    status = request.GET.get("status", "").strip()

    qs = IntakeRequest.objects.all()

    if query:

        qs = qs.filter(

            Q(full_name__icontains=query) | Q(pnfl__icontains=query) | Q(passport__icontains=query) |

            Q(phone__icontains=query) | Q(company__icontains=query) | Q(department__icontains=query)

        )

    if status:

        qs = qs.filter(status=status)

    rows = []

    for item in qs[:250]:

        rows.append({

            "id": item.id,

            "date": timezone.localtime(item.created_at).strftime("%d.%m.%Y %H:%M"),

            "platform": item.platform,

            "cause": item.cause,

            "pnfl": item.pnfl,

            "pnfl_masked": mask_value(item.pnfl),

            "company": item.company,

            "department": item.department,

            "position": item.position,

            "full_name": item.full_name,

            "passport": item.passport,

            "passport_masked": mask_value(item.passport, 2),

            "phone": item.phone,

            "phone_masked": mask_value(item.phone, 4),

            "telegram_id": str(item.telegram_id),

            "telegram_id_masked": mask_value(item.telegram_id, 2),

            "status": item.status,

            "status_label": item.get_status_display(),

            "edit_url": str(reverse_lazy("request_edit", kwargs={"pk": item.pk})), 

        })

    return JsonResponse({"rows": rows, "count": qs.count()})





@login_required

@user_passes_test(user_can_manage)

def request_edit(request, pk):

    item = get_object_or_404(IntakeRequest, pk=pk)

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "delete":
            deleted_id = item.pk
            write_site_log(
                request,
                source="requests",
                action="request_delete",
                message=f"Deleted intake request #{deleted_id}",
                meta={"request_id": deleted_id, "telegram_id": item.telegram_id, "platform": item.platform},
            )
            item.delete()
            messages.success(request, "Заявка удалена.")
            return redirect("requests")

        form = IntakeRequestForm(request.POST, instance=item)

        if form.is_valid():

            item = form.save(commit=False)

            if action in {"generate", "create_user"}:

                item.generated_login = item.generated_login or generate_login(item.full_name, item.pnfl)

                password = generate_password()

                item.generated_password = make_password(password)

                _store_plain_request_password(request, item.pk, password)

            if action == "create_user":

                username = item.generated_login or generate_login(item.full_name, item.pnfl)

                password = _get_plain_request_password(request, item) or generate_password()

                user, _ = User.objects.get_or_create(username=username, defaults={"first_name": item.full_name[:150], "is_active": True})

                user.set_password(password)

                user.save()

                item.django_user = user

                item.generated_login = username

                item.generated_password = make_password(password)

                _store_plain_request_password(request, item.pk, password)

            item.save()

            if action == "send_credentials" and item.generated_login and item.generated_password:

                password = _get_plain_request_password(request, item)

                if not password:

                    messages.error(request, "Пароль хранится только в виде хэша. Сгенерируйте новый пароль и отправьте его сразу.")

                    return redirect("request_edit", pk=item.pk)

                if not _is_django_password_hash(item.generated_password):

                    item.generated_password = make_password(password)

                    item.save(update_fields=["generated_password", "updated_at"])

                send_telegram_message(item.telegram_id, f"Ваш доступ к MTU FORUM:\nЛогин: {item.generated_login}\nПароль: {password}")

                messages.success(request, "Логин и пароль отправлены в Telegram.")

            else:

                messages.success(request, "Заявка сохранена.")

            return redirect("request_edit", pk=item.pk)

    else:

        form = IntakeRequestForm(instance=item)

    plain_generated_password = _get_plain_request_password(request, item)

    return render(request, "request_edit.html", {
        "form": form,
        "item": item,
        "plain_generated_password": plain_generated_password,
        "password_is_hashed": _is_django_password_hash(item.generated_password),
    })





@login_required

@user_passes_test(user_can_manage)

def admin_chat_list(request):
    if request.method == "POST":
        telegram_id = request.POST.get("telegram_id", "").strip()
        title = request.POST.get("title", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        if telegram_id:
            thread = AdminChatThread.objects.create(
                telegram_id=telegram_id,
                title=title,
                full_name=full_name,
                created_by=request.user,
            )
            return redirect("admin_chat_thread_detail", thread_id=thread.pk)

    grouped = AdminChatMessage.objects.values("telegram_id").annotate(

        last_at=Max("created_at"), unread=Count("id", filter=Q(direction=AdminChatMessage.Direction.IN, is_read=False))

    ).order_by("-last_at")

    chats = []

    for thread in AdminChatThread.objects.prefetch_related("messages").all()[:200]:
        last = thread.messages.order_by("-created_at").first()
        unread = thread.messages.filter(direction=AdminChatMessage.Direction.IN, is_read=False).count()
        chats.append({
            "thread_id": thread.id,
            "telegram_id": thread.telegram_id,
            "last": last,
            "unread": unread,
            "full_name": thread.title or thread.full_name or "",
            "status": thread.status,
        })

    for row in grouped:

        last = AdminChatMessage.objects.filter(telegram_id=row["telegram_id"]).order_by("-created_at").first()
        if last and last.thread_id:
            continue

        profile = AdminChatMessage.objects.filter(telegram_id=row["telegram_id"]).exclude(full_name="").order_by("-created_at").first()
        chats.append({"thread_id": None, "telegram_id": row["telegram_id"], "last": last, "unread": row["unread"], "full_name": profile.full_name if profile else "", "status": ""})
    return render(request, "admin_chat_list.html", {"chats": chats})


def _telegram_avatar_svg(telegram_id, label=""):
    safe_label = "".join(ch for ch in (label or str(telegram_id)) if ch.isalnum() or ch.isspace()).strip()
    initials = "".join(part[0] for part in safe_label.split()[:2]).upper() or str(telegram_id)[-2:]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#44d7b6"/><stop offset="1" stop-color="#4f9dff"/></linearGradient></defs>
<rect width="120" height="120" rx="36" fill="#102033"/>
<circle cx="60" cy="60" r="54" fill="url(#g)" opacity=".92"/>
<text x="60" y="72" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" font-weight="700" fill="#061019">{initials[:2]}</text>
</svg>"""


@login_required
@user_passes_test(user_can_manage)
def telegram_profile_photo(request, telegram_id):
    photo = get_telegram_profile_photo(telegram_id)
    if photo:
        content, content_type = photo
        response = HttpResponse(content, content_type=content_type)
        response["Cache-Control"] = "private, max-age=3600"
        return response

    profile = AdminChatMessage.objects.filter(telegram_id=telegram_id).exclude(full_name="").order_by("-created_at").first()
    svg = _telegram_avatar_svg(telegram_id, profile.full_name if profile else "")
    response = HttpResponse(svg, content_type="image/svg+xml")
    response["Cache-Control"] = "private, max-age=300"
    return response


def _admin_chat_thread_for(telegram_id, full_name="", user=None):
    thread = AdminChatThread.objects.filter(telegram_id=telegram_id, status=AdminChatThread.Status.OPEN).order_by("-updated_at").first()
    if thread:
        if full_name and not thread.full_name:
            thread.full_name = full_name
            thread.save(update_fields=["full_name"])
        return thread
    return AdminChatThread.objects.create(telegram_id=telegram_id, full_name=full_name, created_by=user)


def _admin_chat_screen(request, telegram_id, thread=None):
    if thread is None:
        thread = _admin_chat_thread_for(telegram_id, user=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "send")
        if action == "close_chat":
            thread.status = AdminChatThread.Status.CLOSED
            thread.closed_at = timezone.now()
            thread.updated_at = timezone.now()
            thread.save(update_fields=["status", "closed_at", "updated_at"])
            return redirect("admin_chat_list")

        text = request.POST.get("text", "").strip()
        kind = request.POST.get("message_type", AdminChatMessage.Kind.TEXT)
        upload = request.FILES.get("attachment")
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()

        valid_kinds = {choice.value for choice in AdminChatMessage.Kind}
        if kind not in valid_kinds:
            kind = AdminChatMessage.Kind.TEXT

        try:
            if kind == AdminChatMessage.Kind.TEXT:
                if text:
                    AdminChatMessage.objects.create(thread=thread, telegram_id=telegram_id, text=text, kind=kind, direction=AdminChatMessage.Direction.OUT, admin=request.user, is_read=True)
                    send_telegram_message(telegram_id, text)
            elif kind == AdminChatMessage.Kind.LOCATION:
                lat = Decimal(latitude)
                lng = Decimal(longitude)
                AdminChatMessage.objects.create(thread=thread, telegram_id=telegram_id, text=text, kind=kind, latitude=lat, longitude=lng, direction=AdminChatMessage.Direction.OUT, admin=request.user, is_read=True)
                send_telegram_media(telegram_id, kind, caption=text, latitude=str(lat), longitude=str(lng))
            elif upload:
                message = AdminChatMessage.objects.create(
                    thread=thread,
                    telegram_id=telegram_id,
                    text=text,
                    kind=kind,
                    media=upload,
                    media_name=upload.name,
                    direction=AdminChatMessage.Direction.OUT,
                    admin=request.user,
                    is_read=True,
                )
                with message.media.open("rb") as file_obj:
                    send_telegram_media(telegram_id, kind, file_obj=file_obj, filename=message.media_name, caption=text)
            else:
                messages.error(request, "Выберите файл или напишите сообщение.")
            thread.updated_at = timezone.now()
            thread.save(update_fields=["updated_at"])
        except (InvalidOperation, ValueError):
            messages.error(request, "Проверьте координаты.")
        except Exception as exc:
            write_site_log(request, level=SiteLog.Level.ERROR, source="telegram", action="send_media", message=str(exc), status_code=500)
            messages.error(request, "Не удалось отправить сообщение в Telegram. Проверьте Bot Token и логи.")

        return redirect("admin_chat_thread_detail", thread_id=thread.pk)

    messages_qs = AdminChatMessage.objects.filter(Q(thread=thread) | Q(thread__isnull=True, telegram_id=telegram_id))
    messages_qs.filter(direction=AdminChatMessage.Direction.IN).update(is_read=True)
    profile = messages_qs.exclude(full_name="").order_by("-created_at").first()
    return render(request, "admin_chat_detail.html", {
        "chat_messages": messages_qs,
        "telegram_id": telegram_id,
        "chat_name": thread.title or thread.full_name or (profile.full_name if profile else ""),
        "chat_thread": thread,
    })


@login_required
@user_passes_test(user_can_manage)
def admin_chat_thread_detail(request, thread_id):
    thread = get_object_or_404(AdminChatThread, pk=thread_id)
    return _admin_chat_screen(request, thread.telegram_id, thread)





@login_required

@user_passes_test(user_can_manage)

def admin_chat_detail(request, telegram_id):
    return _admin_chat_screen(request, telegram_id)


def _user_display_name(user):
    return user.get_full_name() or user.username


def _internal_chat_title(chat, viewer):
    if chat.title:
        return chat.title
    participants = [item.user for item in chat.participants.all()]
    other_users = [user for user in participants if user != viewer]
    if other_users:
        return ", ".join(_user_display_name(user) for user in other_users[:3])
    return "Избранное"


def _can_manage_internal_chat(user, chat):
    if user.is_staff or user.is_superuser or chat.created_by_id == user.id:
        return True
    return chat.participants.filter(user=user, is_admin=True).exists()


def _find_direct_chat(user, target):
    user_chats = InternalChat.objects.filter(
        chat_type=InternalChat.ChatType.DIRECT,
        is_deleted=False,
        participants__user=user,
    ).prefetch_related("participants")
    expected = {user.id, target.id}
    for chat in user_chats:
        if {item.user_id for item in chat.participants.all()} == expected:
            return chat
    return None


@login_required
def internal_messages_view(request, chat_id=None):
    active_chat = None
    active_membership = None

    if chat_id:
        active_chat = get_object_or_404(
            InternalChat.objects.prefetch_related("participants__user"),
            pk=chat_id,
            is_deleted=False,
            participants__user=request.user,
        )
        active_membership = InternalChatParticipant.objects.filter(chat=active_chat, user=request.user).first()

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "create_direct":
            target = get_object_or_404(User, pk=request.POST.get("user_id"), is_active=True)
            chat = _find_direct_chat(request.user, target)
            if not chat:
                chat = InternalChat.objects.create(chat_type=InternalChat.ChatType.DIRECT, created_by=request.user)
                InternalChatParticipant.objects.bulk_create([
                    InternalChatParticipant(chat=chat, user=request.user, is_admin=True, last_read_at=timezone.now()),
                    InternalChatParticipant(chat=chat, user=target),
                ])
            return redirect("internal_messages_detail", chat_id=chat.pk)

        if action == "create_group":
            title = request.POST.get("title", "").strip() or "Новая группа"
            member_ids = set(request.POST.getlist("member_ids"))
            member_ids.add(str(request.user.id))
            members = list(User.objects.filter(pk__in=member_ids, is_active=True))
            chat = InternalChat.objects.create(title=title, chat_type=InternalChat.ChatType.GROUP, created_by=request.user)
            InternalChatParticipant.objects.bulk_create([
                InternalChatParticipant(chat=chat, user=user, is_admin=(user == request.user), last_read_at=timezone.now() if user == request.user else None)
                for user in members
            ])
            return redirect("internal_messages_detail", chat_id=chat.pk)

        if action == "add_contact":
            target = User.objects.filter(pk=request.POST.get("user_id"), is_active=True).first()
            display_name = request.POST.get("display_name", "").strip() or (_user_display_name(target) if target else "")
            if display_name:
                InternalContact.objects.create(
                    owner=request.user,
                    user=target,
                    display_name=display_name,
                    notes=request.POST.get("notes", "").strip(),
                )
            return redirect("internal_messages")

        if action == "delete_contact":
            InternalContact.objects.filter(pk=request.POST.get("contact_id"), owner=request.user).delete()
            return redirect("internal_messages")

        if not active_chat:
            return redirect("internal_messages")

        if action == "send_message":
            text = request.POST.get("text", "").strip()
            if text:
                InternalChatMessage.objects.create(chat=active_chat, sender=request.user, text=text)
                active_chat.updated_at = timezone.now()
                active_chat.save(update_fields=["updated_at"])
            return redirect("internal_messages_detail", chat_id=active_chat.pk)

        if action == "edit_chat" and active_chat.chat_type == InternalChat.ChatType.GROUP and _can_manage_internal_chat(request.user, active_chat):
            active_chat.title = request.POST.get("title", "").strip() or active_chat.title
            active_chat.updated_at = timezone.now()
            active_chat.save(update_fields=["title", "updated_at"])
            member_ids = set(request.POST.getlist("member_ids"))
            member_ids.add(str(request.user.id))
            current_ids = set(active_chat.participants.values_list("user_id", flat=True))
            desired_ids = set(User.objects.filter(pk__in=member_ids, is_active=True).values_list("id", flat=True))
            InternalChatParticipant.objects.filter(chat=active_chat).exclude(user_id__in=desired_ids).delete()
            for user in User.objects.filter(pk__in=desired_ids - current_ids):
                InternalChatParticipant.objects.create(chat=active_chat, user=user)
            return redirect("internal_messages_detail", chat_id=active_chat.pk)

        if action == "delete_chat":
            if _can_manage_internal_chat(request.user, active_chat):
                active_chat.is_deleted = True
                active_chat.save(update_fields=["is_deleted"])
            else:
                InternalChatParticipant.objects.filter(chat=active_chat, user=request.user).delete()
            return redirect("internal_messages")

        if action in {"edit_message", "delete_message"}:
            message = get_object_or_404(InternalChatMessage, pk=request.POST.get("message_id"), chat=active_chat)
            can_edit = message.sender_id == request.user.id or _can_manage_internal_chat(request.user, active_chat)
            if can_edit and action == "edit_message":
                text = request.POST.get("text", "").strip()
                if text:
                    message.text = text
                    message.edited_at = timezone.now()
                    message.save(update_fields=["text", "edited_at"])
            if can_edit and action == "delete_message":
                message.is_deleted = True
                message.edited_at = timezone.now()
                message.save(update_fields=["is_deleted", "edited_at"])
            return redirect("internal_messages_detail", chat_id=active_chat.pk)

    if active_membership:
        active_membership.last_read_at = timezone.now()
        active_membership.save(update_fields=["last_read_at"])

    chat_queryset = (
        InternalChat.objects.filter(is_deleted=False, participants__user=request.user)
        .prefetch_related("participants__user", "messages")
        .distinct()
    )
    chats = []
    for chat in chat_queryset:
        membership = next((item for item in chat.participants.all() if item.user_id == request.user.id), None)
        last_message = chat.messages.filter(is_deleted=False).order_by("-created_at").first()
        unread_qs = chat.messages.filter(is_deleted=False).exclude(sender=request.user)
        if membership and membership.last_read_at:
            unread_qs = unread_qs.filter(created_at__gt=membership.last_read_at)
        chats.append({
            "item": chat,
            "title": _internal_chat_title(chat, request.user),
            "last": last_message,
            "unread": unread_qs.count(),
            "members": [item.user for item in chat.participants.all()],
        })
    chats.sort(key=lambda row: row["last"].created_at if row["last"] else row["item"].updated_at, reverse=True)

    users = User.objects.filter(is_active=True).exclude(pk=request.user.pk).order_by("first_name", "username")
    contacts = InternalContact.objects.filter(owner=request.user).select_related("user")
    active_messages = active_chat.messages.select_related("sender") if active_chat else []
    active_member_ids = set(active_chat.participants.values_list("user_id", flat=True)) if active_chat else set()

    return render(request, "internal_messages.html", {
        "active_chat": active_chat,
        "active_title": _internal_chat_title(active_chat, request.user) if active_chat else "",
        "active_messages": active_messages,
        "active_member_ids": active_member_ids,
        "can_manage_active_chat": _can_manage_internal_chat(request.user, active_chat) if active_chat else False,
        "chats": chats,
        "contacts": contacts,
        "users": users,
    })





@login_required

def profile(request):

    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    password_form = StyledPasswordChangeForm(request.user)

    avatar_form = UserProfileForm(instance=profile_obj)

    info_form = UserInfoForm(instance=request.user)

    employee_form = EmployeeProfileForm(instance=profile_obj)

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "avatar":

            avatar_form = UserProfileForm(request.POST, request.FILES, instance=profile_obj)

            if avatar_form.is_valid():

                avatar_form.save()

                messages.success(request, "Фото профиля обновлено.")

                return redirect("profile")

            messages.error(request, "Выберите корректное изображение.")

        elif action == "info":

            info_form = UserInfoForm(request.POST, instance=request.user)
            employee_form = EmployeeProfileForm(request.POST, instance=profile_obj)

            if info_form.is_valid() and employee_form.is_valid():

                info_form.save()
                profile_obj = employee_form.save(commit=False)

                if profile_obj.employee_pinfl:

                    profile_obj.pnfl = profile_obj.employee_pinfl

                profile_obj.save()

                messages.success(request, "Данные профиля обновлены.")

                return redirect("profile")

            messages.error(request, "Проверьте имя, фамилию и email.")

        elif action == "employee":

            employee_form = EmployeeProfileForm(request.POST, instance=profile_obj)

            if employee_form.is_valid():

                profile_obj = employee_form.save(commit=False)

                if profile_obj.employee_pinfl:

                    profile_obj.pnfl = profile_obj.employee_pinfl

                profile_obj.save()

                messages.success(request, "Данные сотрудника сохранены.")

                return redirect("profile")

            messages.error(request, "Проверьте данные сотрудника.")

        elif action == "password":

            password_form = StyledPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():

                user = password_form.save()

                update_session_auth_hash(request, user)

                messages.success(request, "Пароль обновлен.")

                return redirect("profile")

            messages.error(request, "Проверьте поля смены пароля.")

    return render(request, "profile.html", {
        "password_form": password_form,
        "avatar_form": avatar_form,
        "info_form": info_form,
        "employee_form": employee_form,
        "profile_obj": profile_obj,
    })





USER_PROFILE_POST_FIELDS = [
    "pnfl",
    "middle_name",
    "phone",
    "birth_date",
    "employee_pinfl",
    "branch",
    "organization",
    "department",
    "position",
]


def _split_hrm_full_name(full_name):
    parts = [part for part in str(full_name or "").split() if part]
    if len(parts) >= 3:
        return parts[0], parts[1], " ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return "", parts[0] if parts else "", ""


def _profile_birth_date(value):
    if not value:
        return None
    if hasattr(value, "year"):
        return value
    text = str(value).strip()
    parsed = parse_date(text[:10])
    if parsed:
        return parsed
    if "." in text:
        day, month, year, *_ = [part.strip() for part in text.split(".")] + ["", ""]
        if day.isdigit() and month.isdigit() and year.isdigit():
            return parse_date(f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}")
    return None


def _ensure_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _hrm_photo_bytes(photo_value):
    photo = str(photo_value or "").strip()
    if not photo:
        return None, ""

    ext = "jpg"
    if photo.startswith("data:image/") and "," in photo:
        header, encoded = photo.split(",", 1)
        content_type = header.split(":", 1)[1].split(";", 1)[0]
        ext = content_type.rsplit("/", 1)[-1] or ext
        content = base64.b64decode(encoded)
    elif photo.startswith(("http://", "https://")):
        response = requests.get(photo, timeout=15, verify=ApiConfiguration.load().hrm_verify_ssl)
        response.raise_for_status()
        content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if content_type.startswith("image/"):
            ext = content_type.rsplit("/", 1)[-1] or ext
        content = response.content
    else:
        encoded = "".join(photo.split())
        content = base64.b64decode(encoded, validate=True)

    if not content or len(content) > 6 * 1024 * 1024:
        raise ValueError("invalid_hrm_photo_size")
    Image.open(BytesIO(content)).verify()
    ext = "jpg" if ext in {"jpeg", "pjpeg"} else ext.split("+", 1)[0]
    if ext not in {"jpg", "png", "webp", "gif", "bmp"}:
        ext = "jpg"
    return content, ext


def _save_hrm_profile_photo(profile, photo_value, *, replace=True):
    photo = str(photo_value or "").strip()
    if photo:
        profile.hrm_photo = photo
    if not photo or (profile.avatar and not replace):
        return False
    try:
        content, ext = _hrm_photo_bytes(photo)
    except Exception as exc:
        write_site_log(
            None,
            level=SiteLog.Level.WARNING,
            source="hrm",
            action="photo_sync",
            message=f"{profile.user.username}: {exc}",
            status_code=502,
        )
        return False
    filename = f"hrm_{profile.user_id}_{timezone.now():%Y%m%d%H%M%S}.{ext}"
    profile.avatar.save(filename, ContentFile(content), save=False)
    return True


def _try_fill_profile_photo_from_hrm(profile):
    if profile.avatar or not profile.pnfl:
        return False
    try:
        hrm = HRMClient().find_employee(profile.pnfl, profile.phone)
    except Exception as exc:
        write_site_log(
            None,
            level=SiteLog.Level.WARNING,
            source="hrm",
            action="photo_lookup",
            message=f"{profile.user.username}: {exc}",
            status_code=502,
        )
        return False
    if not hrm.get("found"):
        return False
    profile.hrm_payload = hrm.get("raw", {}) or profile.hrm_payload
    profile.hrm_synced_at = timezone.now()
    return _save_hrm_profile_photo(profile, hrm.get("photo", ""), replace=False)


def _save_user_profile_from_form(user, form):
    profile = _ensure_user_profile(user)
    for field in USER_PROFILE_POST_FIELDS:
        value = form.cleaned_data.get(field)
        if field == "birth_date":
            setattr(profile, field, _profile_birth_date(value))
        else:
            setattr(profile, field, value or "")
    avatar = form.cleaned_data.get("avatar")
    if avatar:
        profile.avatar = avatar
    elif form.cleaned_data.get("hrm_photo"):
        _save_hrm_profile_photo(profile, form.cleaned_data.get("hrm_photo"), replace=False)
    else:
        _try_fill_profile_photo_from_hrm(profile)
    profile.save()
    return profile


def _hrm_form_initial(hrm, post=None):
    post = post or {}
    full_name = hrm.get("full_name", "")
    last_name = hrm.get("last_name", "")
    first_name = hrm.get("first_name", "")
    middle_name = hrm.get("middle_name", "")
    if full_name and not (last_name or first_name):
        last_name, first_name, middle_name = _split_hrm_full_name(full_name)

    pnfl = hrm.get("pnfl") or hrm.get("employee_pinfl") or post.get("pnfl", "")
    initial = {key: post.get(key, "") for key in [
        "username", "first_name", "last_name", "email", "password", "hrm_photo", *USER_PROFILE_POST_FIELDS,
    ]}
    initial.update({
        "username": post.get("username") or generate_login(full_name or f"{last_name} {first_name}", pnfl),
        "first_name": first_name or post.get("first_name", ""),
        "last_name": last_name or post.get("last_name", ""),
        "middle_name": middle_name or post.get("middle_name", ""),
        "pnfl": pnfl,
        "employee_pinfl": hrm.get("employee_pinfl") or pnfl,
        "phone": hrm.get("phone", "") or post.get("phone", ""),
        "birth_date": _profile_birth_date(hrm.get("birth_date")) or post.get("birth_date", ""),
        "branch": hrm.get("branch", "") or post.get("branch", ""),
        "organization": hrm.get("organization", "") or hrm.get("company", "") or post.get("organization", ""),
        "department": hrm.get("department", "") or post.get("department", ""),
        "position": hrm.get("position", "") or post.get("position", ""),
        "hrm_photo": hrm.get("photo", "") or post.get("hrm_photo", ""),
    })
    return initial


def _apply_hrm_to_user(user, hrm, fallback_pnfl=""):
    last_name = hrm.get("last_name", "")
    first_name = hrm.get("first_name", "")
    middle_name = hrm.get("middle_name", "")
    if hrm.get("full_name") and not (last_name or first_name):
        last_name, first_name, middle_name = _split_hrm_full_name(hrm.get("full_name"))
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.save(update_fields=["first_name", "last_name"])

    pnfl = hrm.get("pnfl") or hrm.get("employee_pinfl") or fallback_pnfl
    profile = _ensure_user_profile(user)
    profile.pnfl = pnfl or profile.pnfl
    profile.employee_pinfl = hrm.get("employee_pinfl") or pnfl or profile.employee_pinfl
    profile.middle_name = middle_name or profile.middle_name
    profile.phone = hrm.get("phone", "") or profile.phone
    profile.birth_date = _profile_birth_date(hrm.get("birth_date")) or profile.birth_date
    profile.branch = hrm.get("branch", "") or profile.branch
    profile.organization = hrm.get("organization", "") or hrm.get("company", "") or profile.organization
    profile.department = hrm.get("department", "") or profile.department
    profile.position = hrm.get("position", "") or profile.position
    _save_hrm_profile_photo(profile, hrm.get("photo", ""), replace=True)
    profile.hrm_payload = hrm.get("raw", {}) or {}
    profile.hrm_synced_at = timezone.now()
    profile.save()
    return profile


def _users_queryset(query=""):
    users = User.objects.select_related("profile").order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__pnfl__icontains=query)
            | Q(profile__middle_name__icontains=query)
            | Q(profile__phone__icontains=query)
            | Q(profile__employee_pinfl__icontains=query)
            | Q(profile__branch__icontains=query)
            | Q(profile__organization__icontains=query)
            | Q(profile__department__icontains=query)
            | Q(profile__position__icontains=query)
        )
    return users


@login_required
@user_passes_test(user_can_administer)
def users_view(request):
    user_form = UserForm()
    query = request.GET.get("q", "").strip()

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("id")
        instance = get_object_or_404(User, pk=user_id) if user_id else None

        if action == "delete" and instance:
            if instance == request.user:
                messages.error(request, "Нельзя удалить текущего пользователя.")
            else:
                username = instance.username
                instance.delete()
                messages.success(request, f"Пользователь {username} удален.")
            return redirect("users")

        if action == "hrm_lookup":
            pnfl = (request.POST.get("pnfl") or request.POST.get("employee_pinfl") or "").strip()
            if not pnfl:
                messages.error(request, "Введите ПНФЛ/ЖШИР для поиска в HRM.")
                user_form = UserForm(initial=request.POST)
            else:
                try:
                    hrm = HRMClient().find_employee(pnfl, request.POST.get("phone", ""))
                except Exception as exc:
                    messages.error(request, f"HRM API недоступен: {exc}")
                    user_form = UserForm(initial=request.POST)
                else:
                    if hrm.get("found"):
                        messages.success(request, "Данные сотрудника получены из HRM.")
                        user_form = UserForm(initial=_hrm_form_initial(hrm, request.POST))
                    else:
                        messages.error(request, hrm.get("message") or NOT_FOUND_MESSAGE)
                        user_form = UserForm(initial=request.POST)
        elif action == "hrm_sync" and instance:
            pnfl = (request.POST.get("pnfl") or request.POST.get("employee_pinfl") or getattr(_ensure_user_profile(instance), "pnfl", "")).strip()
            if not pnfl:
                messages.error(request, "У пользователя нет ПНФЛ/ЖШИР для HRM.")
            else:
                try:
                    hrm = HRMClient().find_employee(pnfl, request.POST.get("phone", ""))
                except Exception as exc:
                    messages.error(request, f"HRM API недоступен: {exc}")
                else:
                    if hrm.get("found"):
                        _apply_hrm_to_user(instance, hrm, fallback_pnfl=pnfl)
                        messages.success(request, "Профиль пользователя обновлен из HRM.")
                    else:
                        messages.error(request, hrm.get("message") or NOT_FOUND_MESSAGE)
            return redirect("users")
        else:
            form = UserForm(request.POST, request.FILES, instance=instance)
            if form.is_valid():
                user = form.save(commit=False)
                password = form.cleaned_data.get("password")
                if password:
                    user.set_password(password)
                elif instance is None:
                    user.set_unusable_password()
                user.save()
                _save_user_profile_from_form(user, form)
                messages.success(request, "Пользователь сохранен.")
                return redirect("users")
            user_form = form if instance is None else UserForm()
            messages.error(request, "Проверьте поля пользователя.")

    users = list(_users_queryset(query))
    for user in users:
        _ensure_user_profile(user)
    return render(request, "users.html", {"users": users, "user_form": user_form, "query": query})


@login_required
@user_passes_test(user_can_administer)
def site_settings_view(request):
    settings_obj = SiteSettings.load()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Настройки сайта сохранены.")
            return redirect("site_settings")
        messages.error(request, "Проверьте поля настроек сайта.")
    else:
        form = SiteSettingsForm(instance=settings_obj)

    return render(request, "site_settings.html", {"form": form, "site_settings_obj": settings_obj})


@login_required
@user_passes_test(user_can_administer)
def site_logs_view(request):
    if request.method == "POST" and request.POST.get("action") == "clear":
        deleted_count = SiteLog.objects.count()
        SiteLog.objects.all().delete()
        write_site_log(request, source="admin", action="logs_clear", message=f"Cleared site logs: {deleted_count}")
        messages.success(request, f"Логи очищены. Удалено записей: {deleted_count}.")
        return redirect("site_logs")

    query = request.GET.get("q", "").strip()
    level = request.GET.get("level", "").strip()
    source = request.GET.get("source", "").strip()
    logs = SiteLog.objects.select_related("user").all()

    if query:
        logs = logs.filter(
            Q(message__icontains=query) |
            Q(path__icontains=query) |
            Q(username__icontains=query) |
            Q(action__icontains=query) |
            Q(source__icontains=query)
        )
    if level:
        logs = logs.filter(level=level)
    if source:
        logs = logs.filter(source=source)

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "site_logs.html", {
        "page_obj": page_obj,
        "levels": SiteLog.Level.choices,
        "sources": SiteLog.objects.order_by("source").values_list("source", flat=True).distinct(),
        "selected_level": level,
        "selected_source": source,
        "query": query,
        "total_logs": logs.count(),
    })


@login_required
@user_passes_test(user_can_administer)
def settings_view(request, section="stations"):
    sections = {"stations", "positions", "platforms", "web-platforms", "channels"}
    if section not in sections:
        return redirect("settings_section", section="stations")

    registry = {
        "station": (Station, StationForm, "Запись", "stations"),
        "position": (Position, PositionForm, "Запись", "positions"),
        "platform": (Platform, PlatformForm, "Платформа", "platforms"),
        "web_platform": (WebPlatform, WebPlatformForm, "WEB платформа", "web-platforms"),
        "channel": (BotSubscriptionChannel, BotSubscriptionChannelForm, "Telegram канал", "channels"),
    }

    if request.method == "POST":

        form_section = request.POST.get("section")

        action = request.POST.get("action")

        model, form_class, label, redirect_section = registry.get(form_section, (None, None, None, "stations"))
        if not model:
            messages.error(request, "Неизвестный справочник.")
            return redirect("settings_section", section="stations")
        instance = get_object_or_404(model, pk=request.POST.get("id")) if request.POST.get("id") else None

        if action == "delete" and instance:
            instance.delete()
            messages.success(request, f"{label.capitalize()} удалена.")
            return redirect("settings_section", section=redirect_section)
        form = form_class(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, f"{label.capitalize()} сохранена.")
            return redirect("settings_section", section=redirect_section)
        messages.error(request, "Проверьте поля формы.")


    return render(request, "settings.html", {
        "stations": Station.objects.all(),
        "positions": Position.objects.all(),
        "platforms": Platform.objects.all(),
        "web_platforms": WebPlatform.objects.all(),
        "channels": BotSubscriptionChannel.objects.all(),
        "active_section": section,
        "station_form": StationForm(),

        "position_form": PositionForm(),

        "platform_form": PlatformForm(),

        "web_platform_form": WebPlatformForm(),

        "channel_form": BotSubscriptionChannelForm(),

    })


def _int_or_zero(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _compact_count(value):
    value = int(value or 0)
    if value >= 1000000:
        return f"{value / 1000000:.1f}".rstrip("0").rstrip(".") + "M"
    if value >= 1000:
        return f"{value / 1000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(value)


def _favicon_url(url):
    parsed = urlparse(url or "")
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def _xlsx_response(section, mode, headers, rows):
    content = build_xlsx(headers, rows)
    filename = f"{section}_{mode}.xlsx"
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@user_passes_test(user_can_administer)
def dictionary_excel_view(request, section, mode):
    configs = {
        "stations": {
            "headers": ["id", "name", "code", "is_active", "sort_order"],
            "sample": [["", "Станция Ахангаран", "AG", "1", "10"]],
        },
        "positions": {
            "headers": ["id", "name", "is_active", "sort_order"],
            "sample": [["", "Начальник станции", "1", "1"]],
        },
        "platforms": {
            "headers": ["id", "name", "code", "is_active", "sort_order"],
            "sample": [["", "MTU FORUM", "mtu_forum", "1", "1"]],
        },
        "web-platforms": {
            "headers": ["id", "name", "url", "image_url", "usage_count", "is_active", "sort_order"],
            "sample": [["", "MTU FORUM WEB", "https://example.com", "https://example.com/favicon.ico", "0", "1", "1"]],
        },
        "channels": {
            "headers": ["id", "name", "url", "telegram_chat_id", "is_required", "is_active", "sort_order"],
            "sample": [["", "MTU FORUM News", "https://t.me/mtu_forum_news", "@mtu_forum_news", "1", "1", "1"]],
        },
    }
    if section not in configs or mode not in {"export", "sample", "import"}:
        messages.error(request, "Неизвестный Excel запрос.")
        return redirect("settings")

    config = configs[section]
    headers = config["headers"]
    if mode == "sample":
        if request.GET.get("download") != "1":
            titles = {
                "stations": "Предприятия",
                "positions": "Должности",
                "platforms": "Платформы",
                "web-platforms": "WEB Платформы",
                "channels": "Telegram каналы",
            }
            return render(request, "excel_sample.html", {
                "section": section,
                "title": titles[section],
                "headers": headers,
                "rows": config["sample"],
            })
        return _xlsx_response(section, "sample", headers, config["sample"])

    if mode == "export":
        if section == "stations":
            rows = [[item.id, item.name, item.code, int(item.is_active), item.sort_order] for item in Station.objects.all()]
        elif section == "positions":
            rows = [[item.id, item.name, int(item.is_active), item.sort_order] for item in Position.objects.all()]
        elif section == "platforms":
            rows = [[item.id, item.name, item.code, int(item.is_active), item.sort_order] for item in Platform.objects.all()]
        elif section == "web-platforms":
            rows = [[item.id, item.name, item.url, item.image_url, item.usage_count, int(item.is_active), item.sort_order] for item in WebPlatform.objects.all()]
        else:
            rows = [[item.id, item.name, item.url, item.telegram_chat_id, int(item.is_required), int(item.is_active), item.sort_order] for item in BotSubscriptionChannel.objects.all()]
        if request.GET.get("download") != "1":
            titles = {
                "stations": "Предприятия",
                "positions": "Должности",
                "platforms": "Платформы",
                "web-platforms": "WEB Платформы",
                "channels": "Telegram каналы",
            }
            return render(request, "excel_export.html", {
                "section": section,
                "title": titles[section],
                "headers": headers,
                "rows": rows[:200],
                "total": len(rows),
            })
        return _xlsx_response(section, "export", headers, rows)

    upload = request.FILES.get("file")
    if request.method != "POST" or not upload:
        messages.error(request, "Выберите Excel файл для импорта.")
        return redirect("settings_section", section=section)

    imported = 0
    with transaction.atomic():
        for row in parse_xlsx(upload):
            row_id = row.get("id")
            name = (row.get("name") or "").strip()
            if not name:
                continue

            if section == "stations":
                instance = Station.objects.filter(pk=row_id).first() if row_id else Station.objects.filter(name=name).first()
                instance = instance or Station()
                instance.name = name
                instance.code = (row.get("code") or "").strip()
                instance.is_active = truthy(row.get("is_active", "1"))
                instance.sort_order = _int_or_zero(row.get("sort_order"))
                instance.save()
            elif section == "positions":
                instance = Position.objects.filter(pk=row_id).first() if row_id else Position.objects.filter(name=name).first()
                instance = instance or Position()
                instance.name = name
                instance.is_active = truthy(row.get("is_active", "1"))
                instance.sort_order = _int_or_zero(row.get("sort_order"))
                instance.save()
            elif section == "platforms":
                instance = Platform.objects.filter(pk=row_id).first() if row_id else Platform.objects.filter(name=name).first()
                instance = instance or Platform()
                instance.name = name
                instance.code = (row.get("code") or "").strip()
                instance.is_active = truthy(row.get("is_active", "1"))
                instance.sort_order = _int_or_zero(row.get("sort_order"))
                instance.save()
            elif section == "web-platforms":
                instance = WebPlatform.objects.filter(pk=row_id).first() if row_id else WebPlatform.objects.filter(name=name).first()
                instance = instance or WebPlatform()
                instance.name = name
                instance.url = (row.get("url") or "").strip()
                instance.image_url = (row.get("image_url") or "").strip()
                instance.usage_count = _int_or_zero(row.get("usage_count"))
                instance.is_active = truthy(row.get("is_active", "1"))
                instance.sort_order = _int_or_zero(row.get("sort_order"))
                instance.save()
            else:
                chat_id = (row.get("telegram_chat_id") or "").strip()
                instance = BotSubscriptionChannel.objects.filter(pk=row_id).first() if row_id else None
                instance = instance or (BotSubscriptionChannel.objects.filter(telegram_chat_id=chat_id).first() if chat_id else None)
                instance = instance or BotSubscriptionChannel()
                instance.name = name
                instance.url = (row.get("url") or "").strip()
                instance.telegram_chat_id = chat_id
                instance.is_required = truthy(row.get("is_required", "1"))
                instance.is_active = truthy(row.get("is_active", "1"))
                instance.sort_order = _int_or_zero(row.get("sort_order"))
                instance.save()
            imported += 1

    messages.success(request, f"Импортировано строк: {imported}.")
    return redirect("settings_section", section=section)


@login_required
@user_passes_test(user_can_administer)
def api_settings_view(request):
    config = ApiConfiguration.load()
    form = ApiConfigurationForm(instance=config)
    external_form = ExternalApiConnectionForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action in {"external_save", "external_delete", "external_test"}:
            instance = get_object_or_404(ExternalApiConnection, pk=request.POST.get("id")) if request.POST.get("id") else None
            if action == "external_delete" and instance:
                instance.delete()
                messages.success(request, "API подключение удалено.")
                return redirect("api_settings")

            if action == "external_test" and instance:
                try:
                    response = _test_external_api_connection(instance)
                except Exception as exc:
                    _remember_external_api_check(instance, error=str(exc))
                    write_site_log(
                        request,
                        level=SiteLog.Level.ERROR,
                        source="external_api",
                        action="connection_test",
                        message=f"{instance.name}: {exc}",
                        status_code=502,
                    )
                    messages.error(request, f"API test failed: {exc}")
                else:
                    if response.status_code < 400:
                        messages.success(request, f"API test OK: HTTP {response.status_code}.")
                    else:
                        messages.warning(request, f"API test returned HTTP {response.status_code}.")
                return redirect("api_settings")

            external_form = ExternalApiConnectionForm(request.POST, instance=instance)
            if external_form.is_valid():
                external_form.save()
                messages.success(request, "API подключение сохранено.")
                return redirect("api_settings")
            messages.error(request, "Проверьте поля API подключения.")
        else:

            form = ApiConfigurationForm(request.POST, instance=config)

            if form.is_valid():
                form.save()
                messages.success(request, "API настройки сохранены.")
                return redirect("api_settings")
            messages.error(request, "Проверьте поля API настроек.")
    return render(request, "api_settings.html", {
        "form": form,
        "config": config,
        "external_form": external_form,
        "external_apis": ExternalApiConnection.objects.all(),
    })


@login_required
@require_GET
def notification_state_api(request):
    can_manage = user_can_manage(request.user)
    settings_obj = SiteSettings.load()
    last_request_id = 0
    last_chat_id = 0
    unread_chats = 0

    if can_manage:
        last_request_id = IntakeRequest.objects.order_by("-id").values_list("id", flat=True).first() or 0
        last_chat_id = AdminChatMessage.objects.filter(direction=AdminChatMessage.Direction.IN).order_by("-id").values_list("id", flat=True).first() or 0
        unread_chats = AdminChatMessage.objects.filter(direction=AdminChatMessage.Direction.IN, is_read=False).count()

    def file_url(field):
        return field.url if field else ""

    language_sounds = {
        "ru": {
            "request": file_url(settings_obj.request_notification_sound_ru) or file_url(settings_obj.request_notification_sound),
            "telegram_chat": file_url(settings_obj.telegram_chat_notification_sound_ru) or file_url(settings_obj.telegram_chat_notification_sound),
            "internal_chat": file_url(settings_obj.internal_chat_notification_sound_ru) or file_url(settings_obj.internal_chat_notification_sound),
        },
        "uz": {
            "request": file_url(settings_obj.request_notification_sound_uz) or file_url(settings_obj.request_notification_sound),
            "telegram_chat": file_url(settings_obj.telegram_chat_notification_sound_uz) or file_url(settings_obj.telegram_chat_notification_sound),
            "internal_chat": file_url(settings_obj.internal_chat_notification_sound_uz) or file_url(settings_obj.internal_chat_notification_sound),
        },
        "uz-cyrl": {
            "request": file_url(settings_obj.request_notification_sound_uz_cyrl) or file_url(settings_obj.request_notification_sound),
            "telegram_chat": file_url(settings_obj.telegram_chat_notification_sound_uz_cyrl) or file_url(settings_obj.telegram_chat_notification_sound),
            "internal_chat": file_url(settings_obj.internal_chat_notification_sound_uz_cyrl) or file_url(settings_obj.internal_chat_notification_sound),
        },
        "en": {
            "request": file_url(settings_obj.request_notification_sound_en) or file_url(settings_obj.request_notification_sound),
            "telegram_chat": file_url(settings_obj.telegram_chat_notification_sound_en) or file_url(settings_obj.telegram_chat_notification_sound),
            "internal_chat": file_url(settings_obj.internal_chat_notification_sound_en) or file_url(settings_obj.internal_chat_notification_sound),
        },
    }

    return JsonResponse({
        "ok": True,
        "enabled": settings_obj.notification_sound_enabled,
        "can_manage": can_manage,
        "last_request_id": last_request_id,
        "last_chat_id": last_chat_id,
        "unread_chats": unread_chats,
        "sounds": {
            "request": file_url(settings_obj.request_notification_sound),
            "telegram_chat": file_url(settings_obj.telegram_chat_notification_sound),
            "internal_chat": file_url(settings_obj.internal_chat_notification_sound),
            "by_language": language_sounds,
        },
    })





def _api_key_valid(request):

    config = ApiConfiguration.load()

    configured_key = config.telegram_api_key or settings.TELEGRAM_API_KEY

    return bool(configured_key) and request.headers.get("X-API-KEY") == configured_key





@csrf_exempt

@require_POST

def telegram_intake_api(request):

    if not _api_key_valid(request):

        return JsonResponse({"ok": False, "error": "invalid api key"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    if not payload.get("pnfl") or not payload.get("telegram_id"):
        return JsonResponse({"ok": False, "error": "pnfl and telegram_id are required"}, status=400)

    try:
        hrm = HRMClient().find_employee(payload.get("pnfl", ""), payload.get("phone", ""))
    except Exception as exc:
        hrm = {"found": False, "message": NOT_FOUND_MESSAGE, "raw": {"error": str(exc)}}
        write_site_log(
            request,
            level=SiteLog.Level.ERROR,
            source="hrm",
            action="check_worker",
            message=str(exc),
            status_code=502,
            meta={"pnfl": payload.get("pnfl", ""), "telegram_id": payload.get("telegram_id")},
        )

    hrm_found = bool(hrm.get("found"))
    selected_position = payload.get("selected_position") or payload.get("position", "")
    selected_company = payload.get("company", "") or payload.get("station", "")
    selected_department = payload.get("department", "")
    reply_via_bot = bool(payload.get("reply_via_bot"))

    if not hrm_found:
        message = hrm.get("message") or NOT_FOUND_MESSAGE
        write_site_log(
            request,
            level=SiteLog.Level.WARNING,
            source="hrm",
            action="worker_not_found",
            message=message,
            status_code=200,
            meta={"pnfl": payload.get("pnfl", ""), "telegram_id": payload.get("telegram_id")},
        )
        telegram_notified = False
        if not reply_via_bot:
            try:
                send_telegram_message(payload.get("telegram_id"), message)
                telegram_notified = True
            except Exception as exc:
                write_site_log(
                    request,
                    level=SiteLog.Level.ERROR,
                    source="telegram",
                    action="send_intake_response",
                    message=str(exc),
                    status_code=502,
                    meta={"pnfl": payload.get("pnfl", ""), "telegram_id": payload.get("telegram_id")},
                )
        return JsonResponse({"ok": False, "hrm_found": False, "message": message, "telegram_notified": telegram_notified})

    item = IntakeRequest.objects.create(

        pnfl=payload.get("pnfl", ""),

        phone=hrm.get("phone") or payload.get("phone", ""),

        telegram_id=payload.get("telegram_id"),

        department=selected_department,

        position=selected_position,

        passport=payload.get("passport", ""),

        lang=payload.get("lang", "ru"),

        cause=payload.get("cause", ""),

        platform=payload.get("platform", ""),

        full_name=payload.get("full_name", "") or hrm.get("full_name", ""),

        company=selected_company or hrm.get("company", ""),

        hrm_payload={"found": hrm_found, "message": hrm.get("message", ""), "raw": hrm.get("raw", {})},

    )

    message = "Ваша заявка принята. Администратор обработает ее в ближайшее время."
    telegram_notified = False
    if reply_via_bot:
        return JsonResponse({"ok": True, "id": item.id, "hrm_found": True, "message": message, "telegram_notified": False})

    try:
        send_telegram_message(item.telegram_id, message)
        telegram_notified = True
    except Exception as exc:
        telegram_notified = False
        write_site_log(
            request,
            level=SiteLog.Level.ERROR,
            source="telegram",
            action="send_intake_response",
            message=str(exc),
            status_code=502,
            meta={"request_id": item.id, "telegram_id": item.telegram_id},
        )

    return JsonResponse({"ok": True, "id": item.id, "hrm_found": hrm_found, "message": message, "telegram_notified": telegram_notified})





@csrf_exempt

@require_POST

def telegram_chat_incoming_api(request):

    if not _api_key_valid(request):

        return JsonResponse({"ok": False}, status=403)

    if request.content_type and request.content_type.startswith("multipart/"):
        payload = request.POST
    else:
        payload = json.loads(request.body.decode("utf-8") or "{}")

    kind = payload.get("message_type", AdminChatMessage.Kind.TEXT)
    valid_kinds = {choice.value for choice in AdminChatMessage.Kind}
    if kind not in valid_kinds:
        kind = AdminChatMessage.Kind.TEXT

    upload = request.FILES.get("attachment")
    thread = None
    if payload.get("thread_id"):
        thread = AdminChatThread.objects.filter(pk=payload.get("thread_id"), telegram_id=payload.get("telegram_id")).first()
    if thread is None:
        thread = _admin_chat_thread_for(payload.get("telegram_id"), full_name=payload.get("full_name", ""))
    create_kwargs = {
        "telegram_id": payload.get("telegram_id"),
        "thread": thread,
        "full_name": payload.get("full_name", ""),
        "text": payload.get("text", ""),
        "kind": kind,
        "direction": AdminChatMessage.Direction.IN,
    }
    if upload:
        create_kwargs["media"] = upload
        create_kwargs["media_name"] = upload.name
    if kind == AdminChatMessage.Kind.LOCATION:
        create_kwargs["latitude"] = payload.get("latitude") or None
        create_kwargs["longitude"] = payload.get("longitude") or None

    msg = AdminChatMessage.objects.create(**create_kwargs)
    thread.updated_at = timezone.now()
    if payload.get("full_name") and not thread.full_name:
        thread.full_name = payload.get("full_name")
        thread.save(update_fields=["updated_at", "full_name"])
    else:
        thread.save(update_fields=["updated_at"])

    return JsonResponse({"ok": True, "id": msg.id})


@csrf_exempt
def telegram_chat_threads_api(request):
    if not _api_key_valid(request):
        return JsonResponse({"ok": False}, status=403)

    if request.method == "GET":
        telegram_id = request.GET.get("telegram_id")
        threads = AdminChatThread.objects.filter(telegram_id=telegram_id, status=AdminChatThread.Status.OPEN).order_by("-updated_at")
        return JsonResponse({
            "ok": True,
            "threads": [
                {"id": item.id, "title": item.title or item.full_name or f"Чат #{item.id}", "updated_at": item.updated_at.isoformat()}
                for item in threads[:10]
            ],
        })

    payload = request.POST or json.loads(request.body.decode("utf-8") or "{}")
    action = payload.get("action")
    telegram_id = payload.get("telegram_id")
    if action == "create":
        thread = AdminChatThread.objects.create(
            telegram_id=telegram_id,
            full_name=payload.get("full_name", ""),
            title=payload.get("title", "") or "Чат с администратором",
        )
        return JsonResponse({"ok": True, "id": thread.id, "title": thread.title})
    if action == "close":
        thread = AdminChatThread.objects.filter(pk=payload.get("thread_id"), telegram_id=telegram_id).first()
        if thread:
            thread.status = AdminChatThread.Status.CLOSED
            thread.closed_at = timezone.now()
            thread.updated_at = timezone.now()
            thread.save(update_fields=["status", "closed_at", "updated_at"])
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": "unknown action"}, status=400)


@require_GET
def telegram_intake_summary_api(request):
    if not _api_key_valid(request):
        return JsonResponse({"ok": False}, status=403)

    telegram_id = request.GET.get("telegram_id")
    qs = IntakeRequest.objects.filter(telegram_id=telegram_id).order_by("-created_at")
    latest = qs.first()
    rows = [
        {
            "id": item.id,
            "date": timezone.localtime(item.created_at).strftime("%d.%m.%Y %H:%M"),
            "platform": item.platform,
            "status": item.get_status_display(),
            "full_name": item.full_name,
            "phone": item.phone,
            "company": item.company,
            "position": item.position,
        }
        for item in qs[:5]
    ]
    pending = [row for row in rows if IntakeRequest.objects.filter(pk=row["id"], status=IntakeRequest.Status.NEW).exists()]
    return JsonResponse({
        "ok": True,
        "latest": rows[0] if latest else None,
        "history": rows,
        "pending": pending,
    })





@require_GET

def public_stations_api(request):

    return JsonResponse({"results": list(Station.objects.filter(is_active=True).values("id", "name", "code"))})





@require_GET

def public_positions_api(request):

    return JsonResponse({"results": list(Position.objects.filter(is_active=True).values("id", "name"))})



@require_GET

def public_platforms_api(request):

    return JsonResponse({"results": list(Platform.objects.filter(is_active=True).values("id", "name", "code"))})



@require_GET

def public_web_platforms_api(request):

    results = [
        {
            "id": item.id,
            "name": item.name,
            "url": item.url,
            "image_url": item.image_url or _favicon_url(item.url),
            "usage_count": item.usage_count,
            "favorite_count": item.favorite_count,
        }
        for item in WebPlatform.objects.filter(is_active=True).annotate(favorite_count=Count("favorites"))
    ]
    return JsonResponse({"results": results})





@require_GET

def public_subscription_channels_api(request):

    qs = BotSubscriptionChannel.objects.filter(is_active=True, is_required=True).values("name", "url", "telegram_chat_id")

    return JsonResponse({"results": list(qs)})





@require_GET

def mobile_config_api(request):

    config = ApiConfiguration.load()

    if not config.mobile_app_enabled:

        return JsonResponse({"ok": False, "error": "mobile app disabled"}, status=403)

    if not config.mobile_api_key or request.headers.get("X-MOBILE-API-KEY") != config.mobile_api_key:

        return JsonResponse({"ok": False, "error": "invalid mobile api key"}, status=403)

    return JsonResponse({

        "ok": True,

        "app_name": config.mobile_app_name,

        "site_base_url": config.site_base_url,

        "stations_url": "/api/public/stations/",

        "positions_url": "/api/public/positions/",

        "platforms_url": "/api/public/platforms/",

        "web_platforms_url": "/api/public/web-platforms/",

    })

