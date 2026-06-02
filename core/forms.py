import re

from django import forms

from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from django.contrib.auth.models import User

from .models import ApiConfiguration, BotSubscriptionChannel, ExternalApiConnection, IntakeRequest, Platform, Position, SiteSettings, Station, UserProfile, WebPlatform





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
    platform = forms.ChoiceField(label="Платформа", widget=forms.Select(attrs={"class": "form-select"}))
    full_name = forms.CharField(label="Ф.И.О", max_length=180, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Фамилия Имя Отчество"}))
    pnfl = forms.CharField(label="ПИНФЛ", max_length=14, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "14 цифр", "inputmode": "numeric"}))
    passport = forms.CharField(label="Паспорт", max_length=9, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "AB1234567"}))
    company = forms.ChoiceField(label="Предприятие", widget=forms.Select(attrs={"class": "form-select"}))
    position = forms.ChoiceField(label="Должность", widget=forms.Select(attrs={"class": "form-select"}))
    phone = forms.CharField(label="Телефон", max_length=32, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+998-XX-XXX-XX-XX"}))
    cause = forms.CharField(label="Причина", max_length=255, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Кратко опишите причину обращения"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["platform"].choices = [("", "Выберите платформу")] + [(item.name, item.name) for item in Platform.objects.filter(is_active=True)]
        self.fields["company"].choices = [("", "Выберите предприятие")] + [(item.name, item.name) for item in Station.objects.filter(is_active=True)]
        self.fields["position"].choices = [("", "Выберите должность")] + [(item.name, item.name) for item in Position.objects.filter(is_active=True)]

    def clean_full_name(self):
        value = re.sub(r"\s+", " ", self.cleaned_data["full_name"]).strip()
        if len(value) < 5:
            raise forms.ValidationError("Введите Ф.И.О полностью.")
        return value

    def clean_pnfl(self):
        value = re.sub(r"\D", "", self.cleaned_data["pnfl"])
        if len(value) != 14:
            raise forms.ValidationError("ПИНФЛ должен состоять из 14 цифр.")
        return value

    def clean_passport(self):
        value = re.sub(r"\s+", "", self.cleaned_data["passport"]).upper()
        if not re.fullmatch(r"[A-Z]{2}\d{7}", value):
            raise forms.ValidationError("Паспорт должен быть в формате AB1234567.")
        return value

    def clean_phone(self):
        digits = re.sub(r"\D", "", self.cleaned_data["phone"])
        if len(digits) == 9:
            digits = f"998{digits}"
        if len(digits) != 12 or not digits.startswith("998"):
            raise forms.ValidationError("Телефон должен быть в формате +998-XX-XXX-XX-XX.")
        return f"+998-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"




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
        user = self.instance if getattr(self.instance, "pk", None) else None
        if user:
            profile = getattr(user, "profile", None)
            if profile:
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

