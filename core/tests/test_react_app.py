import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Branch, IntakeRequest, Organization, SiteRole, Station, UserProfile


@override_settings(FRONTEND_URL="http://frontend.test")
class ReactAppTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("react-admin", password="test-password")

    def test_django_user_routes_redirect_to_standalone_frontend(self):
        self.assertRedirects(self.client.get("/ru/"), "http://frontend.test/app/public/?lang=ru", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/en/login/"), "http://frontend.test/app/login/?lang=en", fetch_redirect_response=False)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get("/ru/requests/"), "http://frontend.test/app/requests/?lang=ru", fetch_redirect_response=False)

    def test_app_route_redirects_instead_of_rendering_html(self):
        response = self.client.get("/app/directories/stations/")
        self.assertRedirects(response, "http://frontend.test/app/directories/stations/?lang=ru", fetch_redirect_response=False)
        self.assertNotIn(b"<html", response.content.lower())

    def test_backend_routes_remain_available(self):
        self.assertEqual(self.client.get(reverse("react_public_api")).status_code, 200)
        self.assertEqual(self.client.get(reverse("react_bootstrap_api")).status_code, 401)
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)

    def test_react_login_and_logout_use_frontend_urls(self):
        self.client.get(reverse("react_captcha_api"))
        answer = self.client.session["react_login_captcha"]["answer"]
        response = self.client.post(reverse("react_login_api"), data=json.dumps({
            "username": "react-admin", "password": "test-password", "captcha_answer": answer,
        }), content_type="application/json")
        self.assertEqual(response.json()["redirect"], "http://frontend.test/app/")
        self.assertEqual(self.client.post(reverse("react_logout_api")).json()["redirect"], "http://frontend.test/app/login/")

    def test_bootstrap_has_no_legacy_interface_links(self):
        self.client.force_login(self.admin)
        payload = self.client.get(reverse("react_bootstrap_api")).json()
        self.assertNotIn("legacy_links", payload)
        self.assertNotIn("version_links", payload)
        self.assertIn("dashboard", payload)

    def test_directory_api_applies_branch_scope(self):
        north = Branch.objects.create(name="North", code="north")
        south = Branch.objects.create(name="South", code="south")
        north_org = Organization.objects.create(branch=north, name="North org", code="north-org")
        south_org = Organization.objects.create(branch=south, name="South org", code="south-org")
        visible = Station.objects.create(branch=north, organization=north_org, name="Visible", code="visible")
        Station.objects.create(branch=south, organization=south_org, name="Hidden", code="hidden")
        role = SiteRole.objects.create(name="Branch manager", code="branch_manager")
        manager = User.objects.create_user("react-branch", password="test-password")
        profile = UserProfile.objects.create(user=manager, branch=north.name)
        profile.roles.add(role)
        self.client.force_login(manager)
        response = self.client.get(reverse("react_directory_api", kwargs={"section": "stations"}))
        self.assertEqual([row["id"] for row in response.json()["rows"]], [visible.id])

    def test_request_editor_api_updates_visible_request(self):
        item = IntakeRequest.objects.create(platform="Platform", cause="Old", pnfl="12345678901234", company="Company", position="Position", full_name="Person", passport="AA1234567", phone="+998901234567", telegram_id=1)
        self.client.force_login(self.admin)
        url = reverse("react_request_api", kwargs={"pk": item.pk})
        self.assertEqual(self.client.get(url).json()["full_name"], "Person")
        response = self.client.patch(url, data=json.dumps({"cause": "Updated", "status": "done"}), content_type="application/json")
        self.assertTrue(response.json()["ok"])
        item.refresh_from_db()
        self.assertEqual((item.cause, item.status), ("Updated", "done"))
