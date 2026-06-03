from django.contrib.auth.models import User

from django.db import models

from django.utils import timezone





class Station(models.Model):

    name = models.CharField(max_length=180, unique=True)

    code = models.CharField(max_length=32, blank=True)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["sort_order", "name"]



    def __str__(self):

        return self.name





class Position(models.Model):

    name = models.CharField(max_length=180, unique=True)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["sort_order", "name"]



    def __str__(self):

        return self.name





class Platform(models.Model):

    name = models.CharField(max_length=180, unique=True)

    code = models.CharField(max_length=32, blank=True)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["sort_order", "name"]



    def __str__(self):

        return self.name





class WebPlatform(models.Model):

    name = models.CharField(max_length=180, unique=True)

    url = models.URLField(max_length=500, blank=True)

    image_url = models.URLField(max_length=500, blank=True)

    usage_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["sort_order", "name"]



    def __str__(self):

        return self.name


class WebPlatformFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="web_platform_favorites")
    platform = models.ForeignKey(WebPlatform, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "platform")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.platform}"



class SiteSettings(models.Model):
    site_name = models.CharField(max_length=120, default="MTU FORUM")
    site_description = models.TextField(blank=True)
    site_tags = models.CharField(max_length=500, blank=True)
    site_logo = models.FileField(upload_to="site/branding/", blank=True)
    site_favicon = models.FileField(upload_to="site/branding/", blank=True)
    site_image = models.FileField(upload_to="site/branding/", blank=True)
    notification_sound_enabled = models.BooleanField(default=True)
    request_notification_sound = models.FileField(upload_to="site/sounds/", blank=True)
    telegram_chat_notification_sound = models.FileField(upload_to="site/sounds/", blank=True)
    internal_chat_notification_sound = models.FileField(upload_to="site/sounds/", blank=True)
    request_notification_sound_ru = models.FileField(upload_to="site/sounds/ru/", blank=True)
    request_notification_sound_uz = models.FileField(upload_to="site/sounds/uz/", blank=True)
    request_notification_sound_uz_cyrl = models.FileField(upload_to="site/sounds/uz-cyrl/", blank=True)
    request_notification_sound_en = models.FileField(upload_to="site/sounds/en/", blank=True)
    telegram_chat_notification_sound_ru = models.FileField(upload_to="site/sounds/ru/", blank=True)
    telegram_chat_notification_sound_uz = models.FileField(upload_to="site/sounds/uz/", blank=True)
    telegram_chat_notification_sound_uz_cyrl = models.FileField(upload_to="site/sounds/uz-cyrl/", blank=True)
    telegram_chat_notification_sound_en = models.FileField(upload_to="site/sounds/en/", blank=True)
    internal_chat_notification_sound_ru = models.FileField(upload_to="site/sounds/ru/", blank=True)
    internal_chat_notification_sound_uz = models.FileField(upload_to="site/sounds/uz/", blank=True)
    internal_chat_notification_sound_uz_cyrl = models.FileField(upload_to="site/sounds/uz-cyrl/", blank=True)
    internal_chat_notification_sound_en = models.FileField(upload_to="site/sounds/en/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.site_name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class IntakeRequest(models.Model):

    class Status(models.TextChoices):

        NEW = "new", "Новая"

        DONE = "done", "Сделано"

        BLOCKED = "blocked", "Заблокирована"



    created_at = models.DateTimeField(default=timezone.now)

    platform = models.CharField(max_length=80, blank=True)

    cause = models.CharField(max_length=255, blank=True)

    pnfl = models.CharField(max_length=32, db_index=True)

    company = models.CharField(max_length=180, blank=True)

    department = models.CharField(max_length=180, blank=True)

    position = models.CharField(max_length=180, blank=True)

    full_name = models.CharField(max_length=180, blank=True, db_index=True)

    passport = models.CharField(max_length=32, blank=True)

    phone = models.CharField(max_length=32, blank=True, db_index=True)

    telegram_id = models.BigIntegerField(db_index=True)

    station = models.CharField(max_length=180, blank=True)

    lang = models.CharField(max_length=8, default="ru")

    generated_login = models.CharField(max_length=150, blank=True)

    generated_password = models.CharField(max_length=150, blank=True)

    django_user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)

    hrm_payload = models.JSONField(default=dict, blank=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:

        ordering = ["-created_at"]



    def __str__(self):

        return f"#{self.pk} {self.full_name or self.pnfl}"





class AdminChatThread(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    telegram_id = models.BigIntegerField(db_index=True)
    full_name = models.CharField(max_length=180, blank=True)
    title = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_admin_chat_threads")

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return self.title or self.full_name or str(self.telegram_id)


class AdminChatMessage(models.Model):

    class Direction(models.TextChoices):

        IN = "in", "От пользователя"

        OUT = "out", "От администратора"

    class Kind(models.TextChoices):
        TEXT = "text", "Text"
        PHOTO = "photo", "Photo"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"
        VOICE = "voice", "Voice"
        VIDEO_NOTE = "video_note", "Round video"
        LOCATION = "location", "Location"



    telegram_id = models.BigIntegerField(db_index=True)

    thread = models.ForeignKey(AdminChatThread, null=True, blank=True, on_delete=models.SET_NULL, related_name="messages")

    full_name = models.CharField(max_length=180, blank=True)

    text = models.TextField(blank=True)

    direction = models.CharField(max_length=8, choices=Direction.choices)

    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.TEXT)

    media = models.FileField(upload_to="chat_uploads/%Y/%m/", blank=True)

    media_name = models.CharField(max_length=255, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    admin = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)



    class Meta:

        ordering = ["created_at"]



    def __str__(self):

        return f"{self.telegram_id}: {self.text[:40]}"


class InternalChat(models.Model):
    class ChatType(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"

    title = models.CharField(max_length=160, blank=True)
    chat_type = models.CharField(max_length=16, choices=ChatType.choices, default=ChatType.DIRECT)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_internal_chats")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return self.title or f"{self.chat_type} #{self.pk}"


class InternalChatParticipant(models.Model):
    chat = models.ForeignKey(InternalChat, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="internal_chat_memberships")
    is_admin = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("chat", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} in {self.chat}"


class InternalChatMessage(models.Model):
    chat = models.ForeignKey(InternalChat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="internal_messages")
    text = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.text[:60]


class InternalContact(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="internal_contacts")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="saved_as_internal_contact")
    display_name = models.CharField(max_length=160)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name





class BotSubscriptionChannel(models.Model):
    name = models.CharField(max_length=160)

    url = models.URLField()

    telegram_chat_id = models.CharField(max_length=120)

    is_required = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)



    class Meta:

        ordering = ["sort_order", "name"]



    def __str__(self):
        return self.name


class SiteLog(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        SECURITY = "security", "Security"

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INFO, db_index=True)
    source = models.CharField(max_length=80, default="system", db_index=True)
    action = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    method = models.CharField(max_length=12, blank=True)
    path = models.CharField(max_length=500, blank=True, db_index=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.level} {self.source}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="profile_avatars/%Y/%m/", blank=True)
    pnfl = models.CharField(max_length=32, blank=True, db_index=True)
    middle_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    employee_pinfl = models.CharField(max_length=32, blank=True, db_index=True)
    branch = models.CharField(max_length=180, blank=True)
    organization = models.CharField(max_length=220, blank=True)
    department = models.CharField(max_length=220, blank=True)
    position = models.CharField(max_length=220, blank=True)
    hrm_photo = models.TextField(blank=True)
    hrm_payload = models.JSONField(default=dict, blank=True)
    hrm_synced_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class ApiConfiguration(models.Model):
    site_base_url = models.URLField(default="http://127.0.0.1:8000")

    telegram_bot_token = models.CharField(max_length=255, blank=True)

    telegram_api_key = models.CharField(max_length=255, blank=True)

    telegram_webhook_url = models.URLField(blank=True)

    mobile_app_name = models.CharField(max_length=120, default="MTU FORUM Mobile")

    mobile_api_key = models.CharField(max_length=255, blank=True)

    mobile_app_base_url = models.URLField(blank=True)

    mobile_app_enabled = models.BooleanField(default=True)

    hrm_base_url = models.URLField(blank=True)

    hrm_client_id = models.CharField(max_length=180, blank=True)

    hrm_public_key = models.CharField(max_length=255, blank=True)

    hrm_secret_type = models.CharField(max_length=120, blank=True)

    hrm_secret = models.CharField(max_length=255, blank=True)

    hrm_verify_ssl = models.BooleanField(default=False)

    # RU: Настройки OneID/E-IMZO хранятся здесь, чтобы администратор менял API без правки кода.
    # UZ: Administrator kodni o'zgartirmasdan API sozlashi uchun OneID/E-IMZO sozlamalari shu yerda saqlanadi.
    # EN: OneID/E-IMZO settings live here so admins can change API values without editing code.
    # RU: Включает/выключает кнопку и backend flow OneID.
    # UZ: OneID tugmasi va backend flowni yoqadi/o'chiradi.
    # EN: Enables/disables the OneID button and backend flow.
    oneid_enabled = models.BooleanField(default=False)

    # RU: client_id выдаётся оператором OneID после регистрации приложения.
    # UZ: client_id ilova ro'yxatdan o'tgandan keyin OneID operatori tomonidan beriladi.
    # EN: client_id is issued by the OneID operator after app registration.
    oneid_client_id = models.CharField(max_length=180, blank=True)

    # RU: client_secret хранится только на backend и никогда не отправляется в браузер.
    # UZ: client_secret faqat backendda saqlanadi va brauzerga yuborilmaydi.
    # EN: client_secret stays on the backend and is never sent to the browser.
    oneid_client_secret = models.CharField(max_length=255, blank=True)

    # RU: Endpoint для первого redirect в OneID, где пользователь выбирает способ входа.
    # UZ: Foydalanuvchi kirish usulini tanlaydigan birinchi OneID redirect endpoint.
    # EN: Endpoint for the first redirect to OneID where the user chooses the login method.
    oneid_authorize_url = models.URLField(default="https://sso.egov.uz/sso/oauth/Authorization.do")

    # RU: Endpoint обмена code на access_token через grant_type=one_authorization_code.
    # UZ: code qiymatini access_tokenga grant_type=one_authorization_code orqali almashtirish endpointi.
    # EN: Endpoint for exchanging code for access_token via grant_type=one_authorization_code.
    oneid_token_url = models.URLField(default="https://sso.egov.uz/sso/oauth/Authorization.do", blank=True)

    # RU: Endpoint получения данных пользователя через grant_type=one_access_token_identify.
    # UZ: grant_type=one_access_token_identify orqali foydalanuvchi ma'lumotlarini olish endpointi.
    # EN: Endpoint for fetching user data via grant_type=one_access_token_identify.
    oneid_userinfo_url = models.URLField(default="https://sso.egov.uz/sso/oauth/Authorization.do", blank=True)

    # RU: scope также выдаётся оператором OneID и должен совпадать с зарегистрированным приложением.
    # UZ: scope ham OneID operatori tomonidan beriladi va ro'yxatdan o'tgan ilova bilan mos bo'lishi kerak.
    # EN: scope is also issued by the OneID operator and must match the registered app.
    oneid_scope = models.CharField(max_length=180, blank=True)

    # RU: Проверка SSL должна быть включена на production.
    # UZ: Production muhitida SSL tekshiruvi yoqilgan bo'lishi kerak.
    # EN: SSL verification should be enabled in production.
    oneid_verify_ssl = models.BooleanField(default=True)

    # RU: Если пользователь OneID найден, но локального аккаунта нет, система может создать его сама.
    # UZ: OneID foydalanuvchisi topilib, lokal akkaunt bo'lmasa, tizim uni o'zi yaratishi mumkin.
    # EN: If a OneID user is found but no local account exists, the system can create it automatically.
    oneid_auto_create_user = models.BooleanField(default=True)

    # RU: Отдельный переключатель для входа через E-IMZO.
    # UZ: E-IMZO orqali kirish uchun alohida yoqish/o'chirish maydoni.
    # EN: Separate switch for E-IMZO login.
    eimzo_enabled = models.BooleanField(default=False)

    # RU: method для E-IMZO redirect; при необходимости меняется под значение, выданное OneID.
    # UZ: E-IMZO redirect uchun method; kerak bo'lsa OneID bergan qiymatga o'zgartiriladi.
    # EN: method for E-IMZO redirect; change it if OneID issues a different value.
    eimzo_oneid_method = models.CharField(max_length=32, default="EIMZO")

    notes = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:

        verbose_name = "API configuration"

        verbose_name_plural = "API configuration"



    def __str__(self):

        return "API configuration MTU FORUM"



    @classmethod

    def load(cls):

        obj, _ = cls.objects.get_or_create(pk=1)

        return obj


class ExternalApiConnection(models.Model):
    class Purpose(models.TextChoices):
        GENERIC = "generic", "Generic API"
        FACE_ID = "face_id", "Face ID"
        HRM = "hrm", "HRM"
        DATA_SYNC = "data_sync", "Data sync"
        NOTIFICATION = "notification", "Notification"

    class Method(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"

    name = models.CharField(max_length=160)
    purpose = models.CharField(max_length=32, choices=Purpose.choices, default=Purpose.GENERIC)
    base_url = models.URLField(max_length=500, blank=True)
    method = models.CharField(max_length=8, choices=Method.choices, default=Method.POST)
    healthcheck_url = models.URLField(max_length=500, blank=True)
    auth_header = models.CharField(max_length=80, default="X-API-KEY")
    api_key = models.CharField(max_length=255, blank=True)
    timeout_seconds = models.PositiveSmallIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    last_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    @property
    def test_url(self):
        return self.healthcheck_url or self.base_url


class DeveloperTask(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новые"
        IN_PROGRESS = "in_progress", "Выполняются"
        DONE = "done", "Выполненные"
        FAILED = "failed", "Не выполненные"
        DONE_LATE = "done_late", "Выполнено с просрочкой"
        APPROVAL = "approval", "На утверждении"
        REVISION = "revision", "Отправленные на доработку"
        RESUMED = "resumed", "Возобновленные"
        FAMILIARIZED = "familiarized", "Ознакомленные"

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_developer_tasks")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_developer_tasks")
    coexecutors = models.ManyToManyField(User, blank=True, related_name="coexecuted_developer_tasks")
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_viewed = models.BooleanField(default=False)
    priority = models.PositiveSmallIntegerField(default=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

