import re

from django import forms

from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from django.contrib.auth.models import User

from .models import ApiConfiguration, BotSubscriptionChannel, DeveloperTask, ExternalApiConnection, IntakeRequest, Platform, Position, SiteRole, SiteSettings, Station, UserProfile, WebPlatform


PUBLIC_INTAKE_TEXTS = {
    "ru": {
        "platform": "Платформа",
        "full_name": "Ф.И.О",
        "full_name_placeholder": "Фамилия Имя Отчество",
        "pnfl": "ПИНФЛ",
        "pnfl_placeholder": "14 цифр",
        "passport": "Паспорт",
        "company": "Предприятие",
        "position": "Должность",
        "phone": "Телефон",
        "cause": "Причина",
        "cause_placeholder": "Кратко опишите причину обращения",
        "select_platform": "Выберите платформу",
        "select_company": "Выберите предприятие",
        "select_position": "Выберите должность",
        "full_name_error": "Введите Ф.И.О полностью.",
        "pnfl_error": "ПИНФЛ должен состоять из 14 цифр.",
        "passport_error": "Паспорт должен быть в формате AB1234567.",
        "phone_error": "Телефон должен быть в формате +998-XX-XXX-XX-XX.",
        "success": "Ваша заявка принята. Администратор обработает ее в ближайшее время.",
        "not_found": "Сервисе проблема с ПНФЛ (Не нашел сотрудника). Попробуйте позже. Или обратитесь в отдел кадров (Приказ, Перевод, и т.д.).",
    },
    "uz": {
        "platform": "Platforma",
        "full_name": "F.I.Sh",
        "full_name_placeholder": "Familiya Ism Otasining ismi",
        "pnfl": "PNFL",
        "pnfl_placeholder": "14 ta raqam",
        "passport": "Pasport",
        "company": "Korxona",
        "position": "Lavozim",
        "phone": "Telefon",
        "cause": "Sabab",
        "cause_placeholder": "Murojaat sababini qisqacha yozing",
        "select_platform": "Platformani tanlang",
        "select_company": "Korxonani tanlang",
        "select_position": "Lavozimni tanlang",
        "full_name_error": "F.I.Shni to'liq kiriting.",
        "pnfl_error": "PNFL 14 ta raqamdan iborat bo'lishi kerak.",
        "passport_error": "Pasport AB1234567 formatida bo'lishi kerak.",
        "phone_error": "Telefon +998-XX-XXX-XX-XX formatida bo'lishi kerak.",
        "success": "Arizangiz qabul qilindi. Administrator uni yaqin vaqt ichida ko'rib chiqadi.",
        "not_found": "Servisda PNFL bilan muammo bor (xodim topilmadi). Keyinroq urinib ko'ring. Yoki kadrlar bo'limiga murojaat qiling (buyruq, o'tkazish va h.k.).",
    },
    "uz-cyrl": {
        "platform": "Платформа",
        "full_name": "Ф.И.Ш",
        "full_name_placeholder": "Фамилия Исм Отасининг исми",
        "pnfl": "ПНФЛ",
        "pnfl_placeholder": "14 та рақам",
        "passport": "Паспорт",
        "company": "Корхона",
        "position": "Лавозим",
        "phone": "Телефон",
        "cause": "Сабаб",
        "cause_placeholder": "Мурожаат сабабини қисқача ёзинг",
        "select_platform": "Платформани танланг",
        "select_company": "Корхонани танланг",
        "select_position": "Лавозимни танланг",
        "full_name_error": "Ф.И.Шни тўлиқ киритинг.",
        "pnfl_error": "ПНФЛ 14 та рақамдан иборат бўлиши керак.",
        "passport_error": "Паспорт AB1234567 форматида бўлиши керак.",
        "phone_error": "Телефон +998-XX-XXX-XX-XX форматида бўлиши керак.",
        "success": "Аризангиз қабул қилинди. Администратор уни яқин вақт ичида кўриб чиқади.",
        "not_found": "Сервисда ПНФЛ билан муаммо бор (ходим топилмади). Кейинроқ уриниб кўринг. Ёки кадрлар бўлимига мурожаат қилинг (буйруқ, ўтказиш ва ҳ.к.).",
    },
    "en": {
        "platform": "Platform",
        "full_name": "Full name",
        "full_name_placeholder": "Surname Name Patronymic",
        "pnfl": "PINFL",
        "pnfl_placeholder": "14 digits",
        "passport": "Passport",
        "company": "Company",
        "position": "Position",
        "phone": "Phone",
        "cause": "Reason",
        "cause_placeholder": "Briefly describe the reason for your request",
        "select_platform": "Select platform",
        "select_company": "Select company",
        "select_position": "Select position",
        "full_name_error": "Enter your full name.",
        "pnfl_error": "PINFL must contain 14 digits.",
        "passport_error": "Passport must be in AB1234567 format.",
        "phone_error": "Phone must be in +998-XX-XXX-XX-XX format.",
        "success": "Your request has been accepted. An administrator will process it soon.",
        "not_found": "There is a service problem with PINFL (employee not found). Try again later or contact HR (order, transfer, etc.).",
    },
}


def public_intake_texts(lang_code):
    lang = (lang_code or "ru").lower()
    if lang in PUBLIC_INTAKE_TEXTS:
        return PUBLIC_INTAKE_TEXTS[lang]
    return PUBLIC_INTAKE_TEXTS.get(lang.split("-")[0], PUBLIC_INTAKE_TEXTS["ru"])





class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Логин"}))

    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}))





class StyledPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs.update({"class": "form-control"})





class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["avatar"]
        widgets = {"avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"})}


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "employee_pinfl",
            "middle_name",
            "phone",
            "birth_date",
            "branch",
            "organization",
            "department",
            "position",
        ]
        widgets = {
            "employee_pinfl": forms.TextInput(attrs={"class": "form-control", "placeholder": "14 цифр"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+998-XX-XXX-XX-XX"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "branch": forms.TextInput(attrs={"class": "form-control"}),
            "organization": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d"]


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class IntakeRequestForm(forms.ModelForm):

    class Meta:

        model = IntakeRequest

        fields = ["pnfl", "full_name", "company", "department", "position", "passport", "phone", "telegram_id", "platform", "cause", "status"]

        widgets = {name: forms.TextInput(attrs={"class": "form-control"}) for name in fields if name != "status"}

        widgets["cause"] = forms.Textarea(attrs={"class": "form-control", "rows": 3})

        widgets["status"] = forms.Select(attrs={"class": "form-select"})

        labels = {
            "pnfl": "ПНФЛ",
            "full_name": "Ф.И.О",
            "company": "Предприятие",
            "department": "Подразделение",
            "position": "Должность",
            "passport": "Паспорт",
            "phone": "Телефон",
            "telegram_id": "Telegram ID",
            "platform": "Платформа",
            "cause": "Причина",
            "status": "Статус",
        }


class SiteIntakeForm(forms.Form):
    platform = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}))
    full_name = forms.CharField(max_length=180, widget=forms.TextInput(attrs={"class": "form-control"}))
    pnfl = forms.CharField(max_length=14, widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}))
    passport = forms.CharField(max_length=9, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "AB1234567"}))
    company = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}))
    position = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}))
    phone = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+998-XX-XXX-XX-XX"}))
    cause = forms.CharField(max_length=255, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))

    def __init__(self, *args, **kwargs):
        self.lang_code = kwargs.pop("lang_code", "ru")
        self.texts = public_intake_texts(self.lang_code)
        super().__init__(*args, **kwargs)
        self.fields["platform"].label = self.texts["platform"]
        self.fields["full_name"].label = self.texts["full_name"]
        self.fields["pnfl"].label = self.texts["pnfl"]
        self.fields["passport"].label = self.texts["passport"]
        self.fields["company"].label = self.texts["company"]
        self.fields["position"].label = self.texts["position"]
        self.fields["phone"].label = self.texts["phone"]
        self.fields["cause"].label = self.texts["cause"]
        self.fields["full_name"].widget.attrs["placeholder"] = self.texts["full_name_placeholder"]
        self.fields["pnfl"].widget.attrs["placeholder"] = self.texts["pnfl_placeholder"]
        self.fields["cause"].widget.attrs["placeholder"] = self.texts["cause_placeholder"]
        self.fields["platform"].choices = [("", self.texts["select_platform"])] + [(item.name, item.name) for item in Platform.objects.filter(is_active=True)]
        self.fields["company"].choices = [("", self.texts["select_company"])] + [(item.name, item.name) for item in Station.objects.filter(is_active=True)]
        self.fields["position"].choices = [("", self.texts["select_position"])] + [(item.name, item.name) for item in Position.objects.filter(is_active=True)]

    def clean_full_name(self):
        value = re.sub(r"\s+", " ", self.cleaned_data["full_name"]).strip()
        if len(value) < 5:
            raise forms.ValidationError(self.texts["full_name_error"])
        return value

    def clean_pnfl(self):
        value = re.sub(r"\D", "", self.cleaned_data["pnfl"])
        if len(value) != 14:
            raise forms.ValidationError(self.texts["pnfl_error"])
        return value

    def clean_passport(self):
        value = re.sub(r"\s+", "", self.cleaned_data["passport"]).upper()
        if not re.fullmatch(r"[A-Z]{2}\d{7}", value):
            raise forms.ValidationError(self.texts["passport_error"])
        return value

    def clean_phone(self):
        digits = re.sub(r"\D", "", self.cleaned_data["phone"])
        if len(digits) == 9:
            digits = f"998{digits}"
        if len(digits) != 12 or not digits.startswith("998"):
            raise forms.ValidationError(self.texts["phone_error"])
        return f"+998-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"




class DeveloperTaskForm(forms.ModelForm):
    class Meta:
        model = DeveloperTask
        fields = ("title", "description", "status", "assignee", "coexecutors", "due_date", "priority", "is_viewed")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название задания"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Описание, детали, ссылки"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "coexecutors": forms.SelectMultiple(attrs={"class": "form-select", "size": 5}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "priority": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "is_viewed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "title": "Название",
            "description": "Описание",
            "status": "Статус",
            "assignee": "Исполнитель",
            "coexecutors": "Соисполнители",
            "due_date": "Срок",
            "priority": "Приоритет",
            "is_viewed": "Просмотрено",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = User.objects.filter(is_active=True).order_by("first_name", "last_name", "username")
        self.fields["assignee"].queryset = users
        self.fields["coexecutors"].queryset = users
        self.fields["assignee"].required = False
        self.fields["coexecutors"].required = False


class AdminStyledModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            css = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"

            if isinstance(field.widget, forms.NumberInput):

                field.widget.attrs.update({"min": 0})

            field.widget.attrs.update({"class": css})





class StationForm(AdminStyledModelForm):

    class Meta:

        model = Station

        fields = ["name", "code", "is_active", "sort_order"]





class PositionForm(AdminStyledModelForm):

    class Meta:

        model = Position

        fields = ["name", "is_active", "sort_order"]



class PlatformForm(AdminStyledModelForm):

    class Meta:

        model = Platform

        fields = ["name", "code", "is_active", "sort_order"]



class SiteRoleForm(AdminStyledModelForm):
    class Meta:
        model = SiteRole
        fields = [
            "name",
            "code",
            "description",
            "is_staff_role",
            "is_admin_role",
            "can_dashboard",
            "can_messages",
            "can_requests",
            "can_chats",
            "can_programmers",
            "can_tasks",
            "can_users",
            "can_directories",
            "can_api_settings",
            "can_site_settings",
            "can_logs",
            "can_profile",
            "is_active",
            "sort_order",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class WebPlatformForm(AdminStyledModelForm):

    class Meta:

        model = WebPlatform

        fields = ["name", "url", "image_url", "usage_count", "is_active", "sort_order"]





class BotSubscriptionChannelForm(AdminStyledModelForm):

    class Meta:

        model = BotSubscriptionChannel

        fields = ["name", "url", "telegram_chat_id", "is_required", "is_active", "sort_order"]





class ApiConfigurationForm(AdminStyledModelForm):

    # RU: Эта форма выводит все API-поля на странице /settings/api/.
    # UZ: Ushbu forma barcha API maydonlarini /settings/api/ sahifasida ko'rsatadi.
    # EN: This form exposes all API fields on the /settings/api/ page.
    class Meta:

        model = ApiConfiguration

        fields = [

            "site_base_url",

            "telegram_bot_token",

            "telegram_api_key",

            "telegram_webhook_url",

            "mobile_app_name",

            "mobile_api_key",

            "mobile_app_base_url",

            "mobile_app_enabled",

            "hrm_base_url",

            "hrm_client_id",

            "hrm_public_key",

            "hrm_secret_type",

            "hrm_secret",

            "hrm_verify_ssl",

            # RU: OneID/E-IMZO поля для реального SSO входа.
            # UZ: Haqiqiy SSO kirish uchun OneID/E-IMZO maydonlari.
            # EN: OneID/E-IMZO fields for the real SSO login flow.
            # RU: Порядок полей совпадает с логикой flow: включение -> credentials -> endpoint -> scope.
            # UZ: Maydonlar tartibi flow mantiqiga mos: yoqish -> credentials -> endpoint -> scope.
            # EN: Field order follows the flow: enable switch -> credentials -> endpoint -> scope.
            "oneid_enabled",

            "oneid_client_id",

            "oneid_client_secret",

            "oneid_authorize_url",

            "oneid_token_url",

            "oneid_userinfo_url",

            "oneid_scope",

            "oneid_verify_ssl",

            "oneid_auto_create_user",

            "eimzo_enabled",

            "eimzo_oneid_method",

            "notes",

        ]

        widgets = {

            "telegram_bot_token": forms.PasswordInput(render_value=True),

            "telegram_api_key": forms.PasswordInput(render_value=True),

            "mobile_api_key": forms.PasswordInput(render_value=True),

            "hrm_secret": forms.PasswordInput(render_value=True),

            "oneid_client_secret": forms.PasswordInput(render_value=True),

            "notes": forms.Textarea(attrs={"rows": 3}),

        }





class ExternalApiConnectionForm(AdminStyledModelForm):
    class Meta:
        model = ExternalApiConnection
        fields = [
            "name",
            "purpose",
            "base_url",
            "method",
            "healthcheck_url",
            "auth_header",
            "api_key",
            "timeout_seconds",
            "is_active",
            "sort_order",
            "notes",
        ]
        widgets = {
            "api_key": forms.PasswordInput(render_value=True),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_timeout_seconds(self):
        timeout = self.cleaned_data.get("timeout_seconds") or 15
        if timeout < 1 or timeout > 120:
            raise forms.ValidationError("Timeout must be between 1 and 120 seconds.")
        return timeout


class SiteSettingsForm(AdminStyledModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "site_name",
            "site_description",
            "site_tags",
            "site_logo",
            "site_favicon",
            "site_image",
            "notification_sound_enabled",
            "request_notification_sound_ru",
            "request_notification_sound_uz",
            "request_notification_sound_uz_cyrl",
            "request_notification_sound_en",
            "telegram_chat_notification_sound_ru",
            "telegram_chat_notification_sound_uz",
            "telegram_chat_notification_sound_uz_cyrl",
            "telegram_chat_notification_sound_en",
            "internal_chat_notification_sound_ru",
            "internal_chat_notification_sound_uz",
            "internal_chat_notification_sound_uz_cyrl",
            "internal_chat_notification_sound_en",
        ]
        widgets = {
            "site_description": forms.Textarea(attrs={"rows": 3, "placeholder": "Короткое описание сайта для браузера, поиска и публичных экранов"}),
            "site_tags": forms.TextInput(attrs={"placeholder": "MTU FORUM, заявки, Telegram, HRM"}),
            "site_logo": forms.FileInput(attrs={"accept": "image/*,.svg"}),
            "site_favicon": forms.FileInput(attrs={"accept": "image/*,.svg,.ico"}),
            "site_image": forms.FileInput(attrs={"accept": "image/*,.svg"}),
            "request_notification_sound_ru": forms.FileInput(attrs={"accept": "audio/*"}),
            "request_notification_sound_uz": forms.FileInput(attrs={"accept": "audio/*"}),
            "request_notification_sound_uz_cyrl": forms.FileInput(attrs={"accept": "audio/*"}),
            "request_notification_sound_en": forms.FileInput(attrs={"accept": "audio/*"}),
            "telegram_chat_notification_sound_ru": forms.FileInput(attrs={"accept": "audio/*"}),
            "telegram_chat_notification_sound_uz": forms.FileInput(attrs={"accept": "audio/*"}),
            "telegram_chat_notification_sound_uz_cyrl": forms.FileInput(attrs={"accept": "audio/*"}),
            "telegram_chat_notification_sound_en": forms.FileInput(attrs={"accept": "audio/*"}),
            "internal_chat_notification_sound_ru": forms.FileInput(attrs={"accept": "audio/*"}),
            "internal_chat_notification_sound_uz": forms.FileInput(attrs={"accept": "audio/*"}),
            "internal_chat_notification_sound_uz_cyrl": forms.FileInput(attrs={"accept": "audio/*"}),
            "internal_chat_notification_sound_en": forms.FileInput(attrs={"accept": "audio/*"}),
        }


class UserForm(AdminStyledModelForm):

    roles = forms.ModelMultipleChoiceField(
        queryset=SiteRole.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    password = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))
    pnfl = forms.CharField(required=False, max_length=32)
    middle_name = forms.CharField(required=False, max_length=120)
    phone = forms.CharField(required=False, max_length=32)
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    employee_pinfl = forms.CharField(required=False, max_length=32)
    branch = forms.CharField(required=False, max_length=180)
    organization = forms.CharField(required=False, max_length=220)
    department = forms.CharField(required=False, max_length=220)
    position = forms.CharField(required=False, max_length=220)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
    hrm_photo = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roles"].queryset = SiteRole.objects.filter(is_active=True).order_by("sort_order", "name")
        user = self.instance if getattr(self.instance, "pk", None) else None
        if user:
            profile = getattr(user, "profile", None)
            if profile:
                self.fields["roles"].initial = profile.roles.all()
                for field in USER_PROFILE_FORM_FIELDS:
                    if field == "avatar":
                        continue
                    self.fields[field].initial = getattr(profile, field, None)



    class Meta:

        model = User

        fields = [
            "username",
            "first_name",
              "last_name",
              "email",
              "roles",
              "is_staff",
            "is_superuser",
            "is_active",
            "password",
            "pnfl",
            "middle_name",
            "phone",
            "birth_date",
            "employee_pinfl",
            "branch",
            "organization",
            "department",
            "position",
            "avatar",
            "hrm_photo",
        ]


USER_PROFILE_FORM_FIELDS = [
    "pnfl",
    "middle_name",
    "phone",
    "birth_date",
    "employee_pinfl",
    "branch",
    "organization",
    "department",
    "position",
    "avatar",
    "hrm_photo",
]

