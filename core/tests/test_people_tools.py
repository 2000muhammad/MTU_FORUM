from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.excel_utils import build_xlsx
from core.models import Branch, Organization, PeopleImportJob, UserPresence
from core.views import USER_EXCEL_HEADERS, _run_user_import_job


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
        self.assertEqual(response.status_code, 200)
        job = PeopleImportJob.objects.get()
        self.assertEqual(job.status, PeopleImportJob.Status.PREVIEW)
        _run_user_import_job(job.pk)
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

    def test_user_form_can_create_branch_manager(self):
        branch = Branch.objects.create(name="Ташкентский филиал")
        response = self.client.post(reverse("users"), {
            "action": "save",
            "username": "branch-manager",
            "first_name": "Менеджер",
            "branch": branch.name,
            "account_type": "branch_manager",
            "is_active": "on",
        })

        self.assertRedirects(response, reverse("users"))
        manager = User.objects.get(username="branch-manager")
        self.assertTrue(manager.is_staff)
        self.assertFalse(manager.is_superuser)
        self.assertEqual(manager.profile.branch, branch.name)
        self.assertTrue(manager.profile.roles.filter(code="branch_manager").exists())

    def test_user_form_can_create_organization_manager(self):
        branch = Branch.objects.create(name="Самаркандский филиал")
        organization = Organization.objects.create(branch=branch, name="Станция Самарканд")
        response = self.client.post(reverse("users"), {
            "action": "save",
            "username": "organization-manager",
            "first_name": "Менеджер",
            "branch": branch.name,
            "organization": organization.name,
            "account_type": "organization_manager",
            "is_active": "on",
        })

        self.assertRedirects(response, reverse("users"))
        manager = User.objects.get(username="organization-manager")
        self.assertTrue(manager.is_staff)
        self.assertFalse(manager.is_superuser)
        self.assertEqual(manager.profile.organization, organization.name)
        self.assertTrue(manager.profile.roles.filter(code="organization_manager").exists())
