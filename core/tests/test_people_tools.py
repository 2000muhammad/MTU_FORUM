from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.excel_utils import build_xlsx
from core.models import UserPresence
from core.views import USER_EXCEL_HEADERS


class PeopleToolsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("people-admin", "admin@example.uz", "secret")
        self.client.force_login(self.admin)

    def test_excel_samples_are_downloadable(self):
        for name in ("users_excel", "manager_accounts_excel"):
            response = self.client.get(reverse(name, args=["sample"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.assertGreater(len(response.content), 1000)

    def test_user_import_creates_account_without_exporting_password(self):
        values = ["imported", "Иван", "Иванов", "user@example.uz", "+998901234567", "", "", "", "", "", "", "yes", "SafePass123!"]
        upload = BytesIO(build_xlsx(USER_EXCEL_HEADERS, [values]))
        upload.name = "users.xlsx"
        response = self.client.post(reverse("users_excel", args=["import"]), {"excel_file": upload})
        self.assertRedirects(response, reverse("users"))
        user = User.objects.get(username="imported")
        self.assertTrue(user.check_password("SafePass123!"))
        export = self.client.get(reverse("users_excel", args=["export"]))
        self.assertNotIn(b"SafePass123!", export.content)

    def test_presence_switches_by_heartbeat_cutoff(self):
        response = self.client.post(reverse("user_presence_heartbeat_api"))
        self.assertEqual(response.status_code, 200)
        state = self.client.get(reverse("user_presence_state_api")).json()
        self.assertTrue(next(item for item in state["users"] if item["id"] == self.admin.id)["online"])
        UserPresence.objects.filter(user=self.admin).update(last_seen_at=timezone.now() - timedelta(minutes=2))
        state = self.client.get(reverse("user_presence_state_api")).json()
        self.assertFalse(next(item for item in state["users"] if item["id"] == self.admin.id)["online"])
