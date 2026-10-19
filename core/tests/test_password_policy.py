from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import UserProfile
from core.password_policy import (
    mark_password_changed,
    mark_temporary_password,
    password_policy_state,
    send_due_password_reminders,
)


class PasswordPolicyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("policy-user", password="old-password")
        self.profile = UserProfile.objects.create(user=self.user, telegram_id=12345)

    def test_regular_password_expires_after_thirty_days(self):
        self.profile.password_changed_at = timezone.now() - timedelta(days=31)
        self.profile.save(update_fields=["password_changed_at"])
        self.assertTrue(password_policy_state(self.user)["required"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("profile") + "?password_expired=1", fetch_redirect_response=False)

    def test_temporary_password_has_fifteen_days_and_change_clears_it(self):
        mark_temporary_password(self.user)
        self.profile.refresh_from_db()
        state = password_policy_state(self.user)
        self.assertTrue(state["temporary"])
        self.assertEqual(state["days_remaining"], 15)

        mark_password_changed(self.user)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.temporary_password_expires_at)
        self.assertFalse(password_policy_state(self.user)["temporary"])

    @patch("core.password_policy.send_telegram_message", return_value={"ok": True})
    def test_temporary_password_reminder_is_sent_only_once_per_day(self, send_message):
        mark_temporary_password(self.user)
        tomorrow = timezone.now() + timedelta(days=1)
        self.assertEqual(send_due_password_reminders(tomorrow), 1)
        self.assertEqual(send_due_password_reminders(tomorrow), 0)
        self.assertEqual(send_message.call_count, 1)

        mark_password_changed(self.user)
        self.assertEqual(send_due_password_reminders(tomorrow + timedelta(days=1)), 0)
