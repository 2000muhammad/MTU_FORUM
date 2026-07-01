import random
import string
from django.contrib.auth.models import User


def mask_value(value, visible=3):
    value = str(value or "")
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * (len(value) - visible * 2)}{value[-visible:]}"


def generate_login(full_name, pnfl):
    base = "".join(ch for ch in (full_name or "user").lower().replace(" ", ".") if ch.isalnum() or ch == ".")
    base = (base.strip(".") or "user")[:32]
    suffix = str(pnfl or random.randint(1000, 9999))[-4:]
    username = f"{base}.{suffix}"
    counter = 1
    candidate = username
    while User.objects.filter(username=candidate).exists():
        counter += 1
        candidate = f"{username}.{counter}"
    return candidate


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(alphabet) for _ in range(length))


def user_is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name="admin").exists():
        return True
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.roles.filter(is_active=True, is_admin_role=True).exists()


def user_has_permission(user, permission):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    if permission == "can_profile":
        return True
    profile = getattr(user, "profile", None)
    if not profile or not hasattr(profile.roles.model, permission):
        return False
    return profile.roles.filter(is_active=True, **{permission: True}).exists()


def user_is_staff_role(user):
    if not user or not user.is_authenticated:
        return False
    if user.groups.filter(name="staff").exists():
        return True
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.roles.filter(is_active=True, is_staff_role=True).exists()


def user_can_manage(user):
    return any((
        user_can_requests(user),
        user_can_chats(user),
        user_can_programmers(user),
        user_can_tasks(user),
        user_can_messages(user),
    ))


def user_can_administer(user):
    return user_is_admin(user)


def user_can_dashboard(user):
    return user_has_permission(user, "can_dashboard")


def user_can_messages(user):
    return user_has_permission(user, "can_messages")


def user_can_requests(user):
    return user_has_permission(user, "can_requests")


def user_can_chats(user):
    return user_has_permission(user, "can_chats")


def user_can_programmers(user):
    return user_has_permission(user, "can_programmers")


def user_can_tasks(user):
    return user_has_permission(user, "can_tasks")


def user_can_directories(user):
    return user_has_permission(user, "can_directories")


def user_can_api_settings(user):
    return user_has_permission(user, "can_api_settings")


def user_can_site_settings(user):
    return user_has_permission(user, "can_site_settings")


def user_can_logs(user):
    return user_has_permission(user, "can_logs")


def user_has_role_code(user, code):
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.roles.filter(code=code, is_active=True).exists()


def user_is_branch_manager(user):
    return user_has_role_code(user, "branch_manager")


def user_is_organization_manager(user):
    return user_has_role_code(user, "organization_manager")


def user_can_manage_people(user):
    return user_has_permission(user, "can_users")


def user_can_manage_manager_accounts(user):
    return user_can_administer(user) or user_is_branch_manager(user)


def user_can_manage_organizations(user):
    return user_can_directories(user) or user_is_branch_manager(user)
