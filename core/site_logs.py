from .models import SiteLog


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def write_site_log(request=None, *, level=SiteLog.Level.INFO, source="system", action="", message="", status_code=None, meta=None):
    try:
        user = getattr(request, "user", None) if request else None
        is_authenticated = bool(user and user.is_authenticated)
        SiteLog.objects.create(
            level=level,
            source=source,
            action=action,
            message=message[:4000],
            method=getattr(request, "method", "") if request else "",
            path=getattr(request, "path", "")[:500] if request else "",
            status_code=status_code,
            ip_address=get_client_ip(request) if request else None,
            user=user if is_authenticated else None,
            username=user.username if is_authenticated else "",
            meta=meta or {},
        )
    except Exception:
        # Logging must never break the user-facing workflow.
        return None
