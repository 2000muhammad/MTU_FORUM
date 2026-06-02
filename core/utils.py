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
    return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name="admin").exists()))


def user_is_staff_role(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.groups.filter(name="staff").exists()))


def user_can_manage(user):
    return user_is_admin(user) or user_is_staff_role(user)


def user_can_administer(user):
    return user_is_admin(user)
