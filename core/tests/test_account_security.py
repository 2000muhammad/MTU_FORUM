import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.forms import StyledPasswordChangeForm
from core.models import Branch, LoginDevice, Organization, PasswordHistory, Platform, Position, SiteRole, Station, UserProfile
from core.password_policy import archive_current_password


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "secure-user", password="Strong-Password-123!", email="secure@example.com"
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def test_last_five_passwords_cannot_be_reused(self):
        archive_current_password(self.user)
        self.user.set_password("Another-Strong-Password-456!")
        self.user.save(update_fields=["password"])
        form = StyledPasswordChangeForm(self.user, {
            "old_password": "Another-Strong-Password-456!",
            "new_password1": "Strong-Password-123!",
            "new_password2": "Strong-Password-123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("последних 5", str(form.errors))
        self.assertEqual(PasswordHistory.objects.filter(user=self.user).count(), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_recovery_sends_temporary_password(self):
        response = self.client.post(
            reverse("react_password_reset_email_api"),
            data=json.dumps({"username": self.user.username}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Временный пароль", mail.outbox[0].body)
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.temporary_password_expires_at, timezone.now() + timedelta(days=14))

    def test_user_can_terminate_another_session(self):
        self.client.force_login(self.user)
        other = SessionStore()
        other["_auth_user_id"] = str(self.user.pk)
        other["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
        other["_auth_user_hash"] = self.user.get_session_auth_hash()
        other.save()
        device = LoginDevice.objects.create(
            user=self.user,
            fingerprint="a" * 64,
            session_key=other.session_key,
            ip_address="127.0.0.2",
        )
        response = self.client.post(reverse("profile"), {
            "action": "terminate_session",
            "device_id": device.pk,
        })
        self.assertRedirects(response, reverse("profile"))
        device.refresh_from_db()
        self.assertFalse(device.is_active)

    def test_profile_shows_assigned_identity_and_access(self):
        role = SiteRole.objects.create(name="Сотрудник теста", code="test-employee")
        platform = Platform.objects.create(name="Платформа профиля")
        branch = Branch.objects.create(name="Филиал профиля")
        organization = Organization.objects.create(name="Организация профиля", branch=branch)
        station = Station.objects.create(name="Предприятие профиля", platform=platform, branch=branch, organization=organization)
        position = Position.objects.create(name="Должность профиля", platform=platform, branch=branch, organization=organization)
        self.profile.roles.add(role)
        self.profile.allowed_platforms.add(platform)
        self.profile.allowed_stations.add(station)
        self.profile.allowed_positions.add(position)
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile"))

        self.assertContains(response, "Данные и доступ пользователя")
        self.assertContains(response, "Сотрудник теста")
        self.assertContains(response, "Платформа профиля")
        self.assertContains(response, "Филиал профиля")
        self.assertContains(response, "Организация профиля")
        self.assertContains(response, "Предприятие профиля")
        self.assertContains(response, "Должность профиля")
