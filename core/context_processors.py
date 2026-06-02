from django.db import DatabaseError, OperationalError, ProgrammingError

from .models import SiteSettings
from .utils import user_can_administer, user_can_manage


def app_ui(request):
    site_settings = None
    try:
        site_settings = SiteSettings.load()
    except (DatabaseError, OperationalError, ProgrammingError):
        site_settings = None

    user = getattr(request, "user", None)
    return {
        "site_settings": site_settings,
        "ui_user_can_manage": user_can_manage(user),
        "ui_user_can_administer": user_can_administer(user),
    }
