import json

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse

from core.forms import IntakeRequestForm
from core.models import AdminChatMessage, Branch, IntakeRequest, Organization, Platform, Position, SiteRole, Station, UserProfile


class RequestPlatformAccessTests(TestCase):
    def setUp(self):
        self.alpha = Platform.objects.create(name="Alpha", code="alpha")
        self.beta = Platform.objects.create(name="Beta", code="beta")
        branch = Branch.objects.create(name="Test branch", code="test-branch")
        organization = Organization.objects.create(name="Test organization", code="test-organization", branch=branch)
        self.allowed_station = Station.objects.create(
            name="Allowed enterprise",
            code="allowed-enterprise",
            branch=branch,
            organization=organization,
        )
        self.denied_station = Station.objects.create(
            name="Denied enterprise",
            code="denied-enterprise",
            branch=branch,
            organization=organization,
        )
        self.role = SiteRole.objects.create(
            name="Request operator",
            code="request_operator",
            can_requests=True,
        )
        self.operator = User.objects.create_user("operator", password="test-password")
        self.profile = UserProfile.objects.create(user=self.operator)
        self.profile.roles.add(self.role)
        self.profile.allowed_platforms.add(self.alpha)
        self.profile.allowed_stations.add(self.allowed_station)
        self.alpha_request = IntakeRequest.objects.create(
            platform=self.alpha.name,
            company=self.allowed_station.name,
            pnfl="11111111111111",
            telegram_id=101,
        )
        self.beta_request = IntakeRequest.objects.create(
            platform=self.beta.name,
            company=self.allowed_station.name,
            pnfl="22222222222222",
            telegram_id=202,
        )
        self.denied_company_request = IntakeRequest.objects.create(
            platform=self.alpha.name,
            company=self.denied_station.name,
            pnfl="33333333333333",
            telegram_id=303,
        )
        self.client.force_login(self.operator)

    def test_request_list_contains_only_assigned_platforms(self):
        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual([row["id"] for row in payload["rows"]], [self.alpha_request.id])
        self.assertNotIn("pnfl", payload["rows"][0])
        self.assertNotIn("phone", payload["rows"][0])

    def test_sensitive_value_requires_current_account_password(self):
        denied = self.client.post(
            reverse("dashboard_request_reveal_api"),
            data=json.dumps({"request_id": self.alpha_request.id, "field": "pnfl", "password": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, 403)

        allowed = self.client.post(
            reverse("dashboard_request_reveal_api"),
            data=json.dumps({
                "request_id": self.alpha_request.id,
                "field": "pnfl",
                "password": "test-password",
            }),
            content_type="application/json",
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["value"], self.alpha_request.pnfl)

    def test_sensitive_value_cannot_be_revealed_outside_scope(self):
        response = self.client.post(
            reverse("dashboard_request_reveal_api"),
            data=json.dumps({
                "request_id": self.beta_request.id,
                "field": "pnfl",
                "password": "test-password",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unassigned_request_cannot_be_opened_directly(self):
        response = self.client.get(reverse("request_edit", kwargs={"pk": self.beta_request.pk}))

        self.assertEqual(response.status_code, 404)

    def test_unassigned_enterprise_request_cannot_be_opened_directly(self):
        response = self.client.get(reverse("request_edit", kwargs={"pk": self.denied_company_request.pk}))

        self.assertEqual(response.status_code, 404)

    def test_operator_can_edit_and_hash_generated_credentials(self):
        response = self.client.post(
            reverse("request_edit", kwargs={"pk": self.alpha_request.pk}),
            {
                "action": "save_credentials",
                "platform": self.alpha.name,
                "company": self.allowed_station.name,
                "pnfl": self.alpha_request.pnfl,
                "telegram_id": self.alpha_request.telegram_id,
                "status": self.alpha_request.status,
                "generated_login": "updated.login",
                "generated_password": "Secure-8421",
            },
        )

        self.assertRedirects(
            response,
            reverse("requests"),
        )
        self.alpha_request.refresh_from_db()
        self.assertEqual(self.alpha_request.generated_login, "updated.login")
        self.assertNotEqual(self.alpha_request.generated_password, "Secure-8421")
        self.assertTrue(check_password("Secure-8421", self.alpha_request.generated_password))

    def test_notification_tracks_only_assigned_platforms(self):
        response = self.client.get(reverse("notification_state_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["last_request_id"], self.alpha_request.id)

    def test_operator_cannot_move_request_to_unassigned_platform(self):
        form = IntakeRequestForm(
            data={
                "platform": self.beta.name,
                "company": self.allowed_station.name,
                "pnfl": self.alpha_request.pnfl,
                "telegram_id": self.alpha_request.telegram_id,
                "status": self.alpha_request.status,
            },
            instance=self.alpha_request,
            user=self.operator,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("platform", form.errors)

    def test_operator_cannot_move_request_to_unassigned_enterprise(self):
        form = IntakeRequestForm(
            data={
                "platform": self.alpha.name,
                "company": self.denied_station.name,
                "pnfl": self.alpha_request.pnfl,
                "telegram_id": self.alpha_request.telegram_id,
                "status": self.alpha_request.status,
            },
            instance=self.alpha_request,
            user=self.operator,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_superuser_can_see_every_platform(self):
        admin = User.objects.create_superuser("admin", password="test-password")
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)


class ManagerRequestScopeTests(TestCase):
    def setUp(self):
        platform = Platform.objects.create(name="Manager platform", code="manager-platform")
        branch_one = Branch.objects.create(name="Branch one", code="branch-one")
        branch_two = Branch.objects.create(name="Branch two", code="branch-two")
        organization_one = Organization.objects.create(
            name="Organization one",
            code="organization-one",
            branch=branch_one,
        )
        organization_two = Organization.objects.create(
            name="Organization two",
            code="organization-two",
            branch=branch_one,
        )
        outside_organization = Organization.objects.create(
            name="Outside organization",
            code="outside-organization",
            branch=branch_two,
        )
        station_one = Station.objects.create(
            name="Enterprise one",
            code="enterprise-one",
            branch=branch_one,
            organization=organization_one,
        )
        station_two = Station.objects.create(
            name="Enterprise two",
            code="enterprise-two",
            branch=branch_one,
            organization=organization_two,
        )
        outside_station = Station.objects.create(
            name="Outside enterprise",
            code="outside-enterprise",
            branch=branch_two,
            organization=outside_organization,
        )
        branch_role = SiteRole.objects.create(
            name="Branch manager",
            code="branch_manager",
            can_requests=True,
        )
        organization_role = SiteRole.objects.create(
            name="Organization manager",
            code="organization_manager",
            can_requests=True,
        )
        self.branch_manager = User.objects.create_user("branch-manager", password="test-password")
        branch_profile = UserProfile.objects.create(user=self.branch_manager, branch=branch_one.name)
        branch_profile.roles.add(branch_role)
        self.organization_manager = User.objects.create_user("organization-manager", password="test-password")
        organization_profile = UserProfile.objects.create(
            user=self.organization_manager,
            branch=branch_one.name,
            organization=organization_one.name,
        )
        organization_profile.roles.add(organization_role)
        self.organization_request = IntakeRequest.objects.create(
            platform=platform.name,
            company=station_one.name,
            pnfl="40000000000001",
            telegram_id=401,
        )
        self.sibling_request = IntakeRequest.objects.create(
            platform=platform.name,
            company=station_two.name,
            pnfl="40000000000002",
            telegram_id=402,
        )
        self.outside_request = IntakeRequest.objects.create(
            platform=platform.name,
            company=outside_station.name,
            pnfl="40000000000003",
            telegram_id=403,
        )

    def test_branch_manager_scope_does_not_drop_requests_with_free_text_positions(self):
        Position.objects.create(
            name="Directory position",
            branch=Branch.objects.get(name="Branch one"),
            organization=Organization.objects.get(name="Organization one"),
        )
        self.organization_request.position = "Position received from Telegram"
        self.organization_request.save(update_fields=["position"])
        self.client.force_login(self.branch_manager)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.organization_request.id, {row["id"] for row in response.json()["rows"]})

    def test_organization_manager_scope_does_not_drop_blank_positions(self):
        Position.objects.create(
            name="Directory position",
            branch=Branch.objects.get(name="Branch one"),
            organization=Organization.objects.get(name="Organization one"),
        )
        self.organization_request.position = ""
        self.organization_request.save(update_fields=["position"])
        self.client.force_login(self.organization_manager)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["rows"]], [self.organization_request.id])

    def test_site_admin_role_sees_all_requests_without_manual_assignments(self):
        admin_role = SiteRole.objects.create(
            name="Site administrator",
            code="site-administrator",
            is_admin_role=True,
            can_requests=True,
        )
        admin = User.objects.create_user("site-admin", password="test-password")
        admin_profile = UserProfile.objects.create(user=admin)
        admin_profile.roles.add(admin_role)
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.json()["rows"]},
            {self.organization_request.id, self.sibling_request.id, self.outside_request.id},
        )

    def test_branch_manager_sees_only_own_branch(self):
        AdminChatMessage.objects.create(
            telegram_id=999,
            direction=AdminChatMessage.Direction.IN,
            text="Restricted chat",
        )
        self.client.force_login(self.branch_manager)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.json()["rows"]},
            {self.organization_request.id, self.sibling_request.id},
        )
        denied = self.client.get(reverse("request_edit", kwargs={"pk": self.outside_request.pk}))
        self.assertEqual(denied.status_code, 404)
        notifications = self.client.get(reverse("notification_state_api")).json()
        self.assertEqual(notifications["last_chat_id"], 0)
        self.assertEqual(notifications["unread_chats"], 0)

    def test_organization_manager_sees_only_own_organization(self):
        self.client.force_login(self.organization_manager)

        response = self.client.get(reverse("dashboard_requests_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in response.json()["rows"]],
            [self.organization_request.id],
        )
        denied = self.client.get(reverse("request_edit", kwargs={"pk": self.sibling_request.pk}))
        self.assertEqual(denied.status_code, 404)

    def test_branch_manager_inherits_organization_manager_request_scope(self):
        self.client.force_login(self.organization_manager)
        organization_rows = self.client.get(reverse("dashboard_requests_api")).json()["rows"]
        organization_request_ids = {row["id"] for row in organization_rows}

        self.client.force_login(self.branch_manager)
        branch_rows = self.client.get(reverse("dashboard_requests_api")).json()["rows"]
        branch_request_ids = {row["id"] for row in branch_rows}

        self.assertTrue(organization_request_ids)
        self.assertTrue(organization_request_ids.issubset(branch_request_ids))
        self.assertNotIn(self.outside_request.id, branch_request_ids)
