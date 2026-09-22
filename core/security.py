import hashlib
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import SecurityThrottle


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")) or "unknown"


def throttle_key(kind, request, username=""):
    raw = f"{kind}|{client_ip(request)}|{str(username).strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_locked(kind, request, username=""):
    row = SecurityThrottle.objects.filter(key=throttle_key(kind, request, username)).first()
    if not row or not row.locked_until:
        return False, 0
    remaining = int((row.locked_until - timezone.now()).total_seconds())
    return remaining > 0, max(0, remaining)


def record_failure(kind, request, username="", *, limit=5, window_minutes=15, lock_minutes=15):
    key = throttle_key(kind, request, username)
    now = timezone.now()
    with transaction.atomic():
        row, _ = SecurityThrottle.objects.select_for_update().get_or_create(key=key, defaults={"kind": kind})
        if now - row.window_started_at > timedelta(minutes=window_minutes):
            row.attempts = 0
            row.window_started_at = now
            row.locked_until = None
        row.attempts += 1
        if row.attempts >= limit:
            row.locked_until = now + timedelta(minutes=lock_minutes)
        row.save()
    return row


def clear_failures(kind, request, username=""):
    SecurityThrottle.objects.filter(key=throttle_key(kind, request, username)).delete()


def consume_rate_limit(kind, request, username="", *, limit=3, window_minutes=15):
    locked, remaining = is_locked(kind, request, username)
    if locked:
        return False, remaining
    row = record_failure(
        kind,
        request,
        username,
        limit=limit + 1,
        window_minutes=window_minutes,
        lock_minutes=window_minutes,
    )
    if row.locked_until:
        return False, int((row.locked_until - timezone.now()).total_seconds())
    return True, 0
