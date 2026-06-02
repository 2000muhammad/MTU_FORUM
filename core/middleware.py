from .models import SiteLog
from .site_logs import write_site_log


class SiteLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as exc:
            write_site_log(
                request,
                level=SiteLog.Level.ERROR,
                source="django",
                action="exception",
                message=f"{exc.__class__.__name__}: {exc}",
                status_code=500,
            )
            raise

        if self._should_log(request, response):
            level = SiteLog.Level.ERROR if response.status_code >= 500 else SiteLog.Level.WARNING if response.status_code >= 400 else SiteLog.Level.INFO
            source = "api" if request.path.startswith("/api/") else "admin"
            write_site_log(
                request,
                level=level,
                source=source,
                action="request",
                message=f"{request.method} {request.path} -> {response.status_code}",
                status_code=response.status_code,
            )
        return response

    def _should_log(self, request, response):
        if request.path.startswith("/static/"):
            return False
        if request.path.endswith("/logs/") and request.method == "GET":
            return False
        if response.status_code >= 400:
            return True
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            return True
        return False
