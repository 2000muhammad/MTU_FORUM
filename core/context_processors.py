from django.db import DatabaseError, OperationalError, ProgrammingError

from .models import SiteSettings
from .utils import (
    user_can_api_settings,
    user_can_administer,
    user_can_chats,
    user_can_dashboard,
    user_can_directories,
    user_can_logs,
    user_can_manage,
    user_can_manage_manager_accounts,
    user_can_manage_organizations,
    user_can_manage_people,
    user_can_messages,
    user_can_programmers,
    user_can_requests,
    user_can_site_settings,
    user_can_tasks,
    user_is_branch_manager,
)


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
        "ui_can_dashboard": user_can_dashboard(user),
        "ui_can_messages": user_can_messages(user),
        "ui_can_requests": user_can_requests(user),
        "ui_can_chats": user_can_chats(user),
        "ui_can_programmers": user_can_programmers(user),
        "ui_can_tasks": user_can_tasks(user),
        "ui_can_directories": user_can_directories(user),
        "ui_can_api_settings": user_can_api_settings(user),
        "ui_can_site_settings": user_can_site_settings(user),
        "ui_can_logs": user_can_logs(user),
        "ui_user_can_manage_people": user_can_manage_people(user),
        "ui_user_can_manage_manager_accounts": user_can_manage_manager_accounts(user),
        "ui_user_can_manage_organizations": user_can_manage_organizations(user),
        "ui_user_is_branch_manager": user_is_branch_manager(user),
    }
