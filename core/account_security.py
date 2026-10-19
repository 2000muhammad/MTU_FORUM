import hashlib

from django.core.mail import send_mail
from django.utils import timezone

from .models import LoginDevice
from .security import client_ip
from .telegram import send_telegram_message


def register_login_device(request, user):
    if not request.session.session_key:
        request.session.save()
    ip = client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
    fingerprint = hashlib.sha256(f"{ip}|{user_agent}".encode("utf-8")).hexdigest()
    device, created = LoginDevice.objects.get_or_create(
        user=user,
        fingerprint=fingerprint,
        defaults={"ip_address": None if ip == "unknown" else ip, "user_agent": user_agent},
    )
    device.session_key = request.session.session_key or ""
    device.ip_address = None if ip == "unknown" else ip
    device.user_agent = user_agent
    device.last_seen_at = timezone.now()
    device.is_active = True
    device.save(update_fields=["session_key", "ip_address", "user_agent", "last_seen_at", "is_active"])
    if created:
        text = (
            "🔐 <b>Новый вход в MTU FORUM</b>\n\n"
            f"IP-адрес: {ip}\n"
            f"Устройство: {user_agent or 'Не определено'}\n"
            f"Время: {timezone.localtime():%d.%m.%Y %H:%M}\n\n"
            "Если это были не вы, смените пароль и завершите другие сеансы."
        )
        profile = getattr(user, "profile", None)
        if profile and profile.telegram_id:
            try:
                send_telegram_message(profile.telegram_id, text)
            except Exception:
                pass
        if user.email:
            try:
                send_mail(
                    "Новый вход в MTU FORUM",
                    text.replace("<b>", "").replace("</b>", ""),
                    None,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
    return device, created
