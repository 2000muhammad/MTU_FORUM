import re

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from core.models import SiteRole, UserProfile


class RandomPasswordResetTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("password-admin", password="admin-password")
        self.client.force_login(self.admin)

    def _password_from_messages(self, response):
        text = " ".join(str(message) for message in get_messages(response.wsgi_request))
        match = re.search(r"(?:Пароль|пароль[^:]*): ([A-Za-z0-9]+)", text)
        self.assertIsNotNone(match, text)
        return match.group(1)

    def test_user_reset_generates_and_displays_random_password(self):
        user = User.objects.create_user("ordinary-user", password="old-password")
        response = self.client.post(reverse("users"), {"action": "reset_password", "id": user.pk}, follow=True)
        password = self._password_from_messages(response)
        user.refresh_from_db()
        self.assertEqual(len(password), 12)
        self.assertNotEqual(password, "1234567")
        self.assertTrue(user.check_password(password))

    def test_manager_reset_generates_and_displays_random_password(self):
        role = SiteRole.objects.create(name="Branch manager", code="branch_manager")
        manager = User.objects.create_user("branch-manager", password="old-password", is_staff=True)
        profile = UserProfile.objects.create(user=manager)
        profile.roles.add(role)
        response = self.client.post(reverse("manager_accounts"), {"action": "reset_password", "id": manager.pk}, follow=True)
        password = self._password_from_messages(response)
        manager.refresh_from_db()
        self.assertEqual(len(password), 12)
        self.assertNotEqual(password, "1234567")
        self.assertTrue(manager.check_password(password))
