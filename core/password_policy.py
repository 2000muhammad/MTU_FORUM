from datetime import timedelta
from math import ceil

from django.utils import timezone

from .models import UserProfile
from .telegram import send_telegram_message


PASSWORD_LIFETIME_DAYS = 30
TEMPORARY_PASSWORD_LIFETIME_DAYS = 15


def password_policy_state(user, now=None):
    now = now or timezone.now()
    profile = getattr(user, "profile", None)
    if not profile or not user.has_usable_password():
        return {"required": False, "show_warning": False}

    temporary = bool(profile.temporary_password_expires_at)
    deadline = profile.temporary_password_expires_at if temporary else (
        profile.password_changed_at + timedelta(days=PASSWORD_LIFETIME_DAYS)
    )
    seconds_left = (deadline - now).total_seconds()
    days_remaining = max(0, ceil(seconds_left / 86400))
    required = seconds_left <= 0
    if temporary:
        message = (
            "Срок временного пароля истёк. Смените пароль в профиле."
            if required
            else f"После восстановления смените временный пароль. Осталось дней: {days_remaining}."
        )
    else:
        message = (
            "Срок действия пароля истёк. Для продолжения работы смените пароль."
            if required
            else f"Срок действия пароля: ещё {days_remaining} дн."
        )
    return {
        "required": required,
        "temporary": temporary,
        "days_remaining": days_remaining,
        "deadline": deadline.isoformat(),
        "show_warning": temporary or days_remaining <= 5,
        "message": message,
    }


def mark_password_changed(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.password_changed_at = timezone.now()
    profile.temporary_password_expires_at = None
    profile.password_reminder_sent_on = None
    profile.save(update_fields=[
        "password_changed_at", "temporary_password_expires_at",
        "password_reminder_sent_on", "updated_at",
    ])
    return profile


def mark_temporary_password(user):
    now = timezone.now()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.password_changed_at = now
    profile.temporary_password_expires_at = now + timedelta(days=TEMPORARY_PASSWORD_LIFETIME_DAYS)
    profile.password_reminder_sent_on = now.date()
    profile.save(update_fields=[
        "password_changed_at", "temporary_password_expires_at",
        "password_reminder_sent_on", "updated_at",
    ])
    return profile


def send_due_password_reminders(now=None):
    now = now or timezone.now()
    sent = 0
    profiles = UserProfile.objects.select_related("user").filter(
        user__is_active=True,
        telegram_id__isnull=False,
        temporary_password_expires_at__isnull=False,
    ).exclude(password_reminder_sent_on=now.date())
    for profile in profiles:
        state = password_policy_state(profile.user, now)
        result = send_telegram_message(
            profile.telegram_id,
            "🔐 <b>Необходимо сменить пароль MTU FORUM</b>\n\n"
            f"{state['message']}\n"
            "После смены пароля напоминания прекратятся.",
        )
        if result.get("ok"):
            profile.password_reminder_sent_on = now.date()
            profile.save(update_fields=["password_reminder_sent_on", "updated_at"])
            sent += 1
    return sent
