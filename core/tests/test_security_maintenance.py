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
            self.client.post("/ru/login/?legacy=1", {"username": self.user.username, "password": "wrong"})
        response = self.client.post(
            "/ru/login/?legacy=1",
            {"username": self.user.username, "password": "correct-password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertTrue(SecurityThrottle.objects.filter(kind="login", locked_until__gt=timezone.now()).exists())
        self.assertTrue(SiteLog.objects.filter(action="login_locked").exists())

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
