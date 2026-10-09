import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import SecurityThrottle, SiteLog, UserProfile


class LoginSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("secure-user", password="correct-password")

    def test_legacy_login_is_temporarily_locked_after_failures(self):
        for _ in range(5):
            self.client.get("/ru/login/?legacy=1")
            answer = self.client.session["react_login_captcha"]["answer"]
            self.client.post("/ru/login/?legacy=1", {"username": self.user.username, "password": "wrong", "captcha_answer": answer})
        self.client.get("/ru/login/?legacy=1")
        answer = self.client.session["react_login_captcha"]["answer"]
        response = self.client.post(
            "/ru/login/?legacy=1",
            {"username": self.user.username, "password": "correct-password", "captcha_answer": answer},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertTrue(SecurityThrottle.objects.filter(kind="login", locked_until__gt=timezone.now()).exists())
        self.assertTrue(SiteLog.objects.filter(action="login_locked").exists())

    def test_legacy_login_requires_one_time_captcha(self):
        page = self.client.get("/ru/login/?legacy=1")
        self.assertContains(page, "name=\"captcha_answer\"")
        answer = self.client.session["react_login_captcha"]["answer"]
        success = self.client.post(
            "/ru/login/?legacy=1",
            {"username": self.user.username, "password": "correct-password", "captcha_answer": answer},
        )
        self.assertEqual(success.status_code, 302)

    @override_settings(TELEGRAM_BOT_USERNAME="test_bot")
    def test_password_reset_rate_limit_allows_three_requests(self):
        UserProfile.objects.create(
            user=self.user,
            phone="+998901234567",
            telegram_id=7788,
            telegram_phone="+998901234567",
            telegram_verified_at=timezone.now(),
        )
        statuses = []
        for _ in range(4):
            response = self.client.post(
                reverse("react_password_reset_request_api"),
                data=json.dumps({"username": self.user.username}),
                content_type="application/json",
            )
            statuses.append(response.status_code)
        self.assertEqual(statuses, [200, 200, 200, 429])


class AutomatedMaintenanceTests(TestCase):
    def test_command_creates_backup_and_logs_health(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Mock(ok=True, status_code=200)
            with override_settings(BASE_DIR=Path(directory), TELEGRAM_BOT_TOKEN="token"), patch(
                "core.management.commands.automated_maintenance.requests.get", return_value=response
            ):
                call_command("automated_maintenance", verbosity=0)
            self.assertEqual(len(list((Path(directory) / "backups").glob("mtu-forum-*.json"))), 1)
        self.assertTrue(SiteLog.objects.filter(action="automatic_backup").exists())
        self.assertTrue(SiteLog.objects.filter(action="telegram_health").exists())


class SiteLogCategoryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("log-admin", password="test-password")
        SiteLog.objects.create(source="requests", action="request_delete", message="Request removed")
        SiteLog.objects.create(source="people", action="user_delete", message="User removed")
        SiteLog.objects.create(source="auth", action="login_failed", message="Login failed")
        self.client.force_login(self.admin)

    def test_request_log_page_only_contains_request_events(self):
        response = self.client.get(reverse("site_logs_category", kwargs={"category": "requests"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request removed")
        self.assertNotContains(response, "User removed")
        self.assertContains(response, "Заявки")

    def test_user_log_page_only_contains_user_events(self):
        response = self.client.get(reverse("site_logs_category", kwargs={"category": "users"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User removed")
        self.assertNotContains(response, "Request removed")

    def test_unknown_category_falls_back_to_all_events(self):
        response = self.client.get(reverse("site_logs_category", kwargs={"category": "unknown"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request removed")
        self.assertContains(response, "User removed")
