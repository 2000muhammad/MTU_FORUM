import threading

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command


def _run_maintenance():
    try:
        call_command("automated_maintenance")
    except Exception:
        # The scheduled task must never break a user request.
        pass


class AutoMaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.AUTO_MAINTENANCE_ENABLED:
            acquired = cache.add("mtu:auto-maintenance", "running", timeout=settings.AUTO_MAINTENANCE_INTERVAL)
            if acquired:
                threading.Thread(target=_run_maintenance, name="mtu-maintenance", daemon=True).start()
        return self.get_response(request)
