import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Branch, Organization, Position, SiteRole, Station, UserProfile


class ReactAppTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("react-admin", password="test-password")

    def test_react_app_is_available_for_public_login_and_request_routes(self):
        response = self.client.get(reverse("react_app_global"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/next/_next/")
        self.assertEqual(self.client.get("/app/login/").status_code, 200)
        self.assertEqual(self.client.get("/app/public/").status_code, 200)
        bootstrap = self.client.get(reverse("react_bootstrap_api"))
        self.assertEqual(bootstrap.status_code, 401)
        self.assertEqual(bootstrap.json()["login_url"], "/app/login/")

    def test_react_app_and_nested_route_render_bundle(self):
        self.client.force_login(self.admin)

        root = self.client.get(reverse("react_app_global"))
        nested = self.client.get(reverse("react_app_global_path", kwargs={"path": "directories/stations"}))

        self.assertContains(root, "/static/next/_next/")
        self.assertEqual(nested.status_code, 200)

    def test_localized_app_redirects_to_global_next_app(self):
        self.client.force_login(self.admin)

        response = self.client.get("/en/app/")

        self.assertRedirects(response, reverse("react_app_global"), fetch_redirect_response=False)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

        nested = self.client.get("/uz/app/requests/")
        self.assertRedirects(nested, "/app/requests", fetch_redirect_response=False)
        self.assertEqual(nested.cookies[settings.LANGUAGE_COOKIE_NAME].value, "uz")

    def test_public_and_login_pages_redirect_to_react(self):
        public_response = self.client.get("/ru/")
        login_response = self.client.get("/ru/login/")

        self.assertRedirects(public_response, "/app/public/?lang=ru", fetch_redirect_response=False)
        self.assertRedirects(login_response, "/app/login/?lang=ru", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/ru/?legacy=1").status_code, 200)
        self.assertEqual(self.client.get("/ru/login/?legacy=1").status_code, 200)
        self.assertContains(self.client.get("/ru/?legacy=1"), "/app/public/?lang=ru")
        self.assertContains(self.client.get("/ru/login/?legacy=1"), "/app/login/?lang=ru")

    def test_react_public_api_and_login(self):
        public_response = self.client.get(reverse("react_public_api"), {"lang": "ru"})
        self.assertEqual(public_response.status_code, 200)
        self.assertIn("choices", public_response.json())

        captcha_response = self.client.get(reverse("react_captcha_api"))
        self.assertEqual(captcha_response.status_code, 200)
        self.assertIn("question", captcha_response.json())
        captcha_answer = self.client.session["react_login_captcha"]["answer"]

        login_response = self.client.post(
            reverse("react_login_api"),
            data=json.dumps({
                "username": "react-admin",
                "password": "test-password",
                "remember_me": True,
                "captcha_answer": captcha_answer,
            }),
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["ok"])
        self.assertEqual(login_response.json()["redirect"], reverse("react_app_global"))

    def test_react_login_rejects_missing_or_wrong_captcha(self):
        missing = self.client.post(
            reverse("react_login_api"),
            data=json.dumps({"username": "react-admin", "password": "test-password"}),
            content_type="application/json",
        )
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.json()["error_code"], "captcha_invalid")
        self.assertFalse(self.client.session.get("_auth_user_id"))

        self.client.get(reverse("react_captcha_api"))
        wrong = self.client.post(
            reverse("react_login_api"),
            data=json.dumps({
                "username": "react-admin",
                "password": "test-password",
                "captcha_answer": -999,
            }),
            content_type="application/json",
        )
        self.assertEqual(wrong.status_code, 400)
        self.assertTrue(wrong.json()["captcha_refresh"])
        self.assertNotIn("react_login_captcha", self.client.session)

    def test_legacy_login_keeps_the_selected_version(self):
        response = self.client.post(
            "/ru/login/?legacy=1",
            {"username": "react-admin", "password": "test-password"},
        )

        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_platform_version_choice_persists_until_explicitly_changed(self):
        legacy = self.client.get("/ru/?legacy=1")
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.cookies["mtu_platform_version"].value, "legacy")

        legacy_again = self.client.get("/ru/")
        self.assertEqual(legacy_again.status_code, 200)

        react = self.client.get(reverse("react_app_global"))
        self.assertEqual(react.cookies["mtu_platform_version"].value, "react")
        switched = self.client.get("/ru/")
        self.assertRedirects(
            switched,
            "/app/public/?lang=ru",
            fetch_redirect_response=False,
        )

    def test_react_public_api_localizes_form_choices(self):
        response = self.client.get(reverse("react_public_api"), {"lang": "en"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["texts"]["full_name"], "Full name")
        self.assertEqual(payload["choices"]["platforms"][0]["label"], "Select platform")

    def test_react_bootstrap_contains_permissions_and_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("react_bootstrap_api"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["user"]["username"], self.admin.username)
        self.assertEqual(payload["language"], "ru")
        self.assertTrue(payload["permissions"]["directories"])
        self.assertIn("stats", payload["dashboard"])
        self.assertEqual(
            payload["version_links"]["old"],
            f'{reverse("dashboard")}?legacy=1',
        )
        self.assertEqual(payload["version_links"]["new"], reverse("react_app_global"))
        for module in ("messages", "chats", "tasks", "users", "managers", "settings", "api_settings", "site_settings", "logs", "programmers", "profile"):
            self.assertIn(module, payload["legacy_links"])

    def test_legacy_page_has_both_version_links(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Старая версия")
        self.assertContains(response, "Новая версия")
        self.assertNotContains(response, "Новая версия (Next.js)")
        self.assertContains(response, f'href="{reverse("react_app_global")}"')

    def test_legacy_version_toggle_is_localized(self):
        public_response = self.client.get("/uz/?legacy=1")

        self.assertContains(public_response, "Eski versiya")
        self.assertContains(public_response, "Yangi versiya")
        self.assertContains(public_response, 'class="version-toggle is-old"')
        self.assertNotContains(public_response, ">Старая версия<")

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

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["rows"]], [visible.id])

    def test_production_bundle_exists(self):
        static_dir = Path(settings.BASE_DIR) / "static" / "next"

        self.assertTrue((static_dir / "index.html").is_file())
        self.assertTrue((static_dir / "_next").is_dir())

    def test_legacy_pages_allow_only_same_origin_embedding(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("profile") + "?embedded=1")

        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertContains(response, "embedded-react-view")

    def test_all_platform_modules_render_inside_react_workspace(self):
        self.client.force_login(self.admin)

        route_names = (
            "internal_messages", "admin_chat_list", "developer_tasks", "users",
            "manager_accounts", "settings", "api_settings", "site_settings",
            "site_logs", "programmers", "profile",
        )
        for route_name in route_names:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name), {"embedded": "1"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")

        module_page = self.client.get(
            reverse("react_app_global_path", kwargs={"path": "modules/users"})
        )
        self.assertEqual(module_page.status_code, 200)
        self.assertContains(module_page, "/static/next/_next/")
