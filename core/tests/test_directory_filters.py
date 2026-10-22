from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Branch, Organization, Platform, Position, SiteRole, Station, UserProfile
from core.utils import user_can_api_settings, user_can_site_settings


class DirectoryFilterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("directory-admin", password="test-password")
        self.client.force_login(self.admin)
        self.branch_one = Branch.objects.create(name="North branch", code="north")
        self.branch_two = Branch.objects.create(name="South branch", code="south")
        self.organization_one = Organization.objects.create(
            branch=self.branch_one,
            name="North organization",
            code="north-org",
        )
        self.organization_two = Organization.objects.create(
            branch=self.branch_two,
            name="South organization",
            code="south-org",
        )
        self.active_station = Station.objects.create(
            branch=self.branch_one,
            organization=self.organization_one,
            name="Central enterprise",
            code="central-enterprise",
        )
        self.inactive_station = Station.objects.create(
            branch=self.branch_two,
            organization=self.organization_two,
            name="Remote enterprise",
            code="remote-enterprise",
            is_active=False,
        )
        self.north_position = Position.objects.create(
            branch=self.branch_one,
            organization=self.organization_one,
            name="North engineer",
        )
        self.south_position = Position.objects.create(
            branch=self.branch_two,
            organization=self.organization_two,
            name="South engineer",
        )

    def test_station_search_and_status_filter(self):
        response = self.client.get(
            reverse("settings_section", kwargs={"section": "stations"}),
            {"station_q": "Remote", "station_status": "inactive"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["station_rows"].object_list), [self.inactive_station])

    def test_station_branch_filter(self):
        response = self.client.get(
            reverse("settings_section", kwargs={"section": "stations"}),
            {"station_branch": self.branch_one.pk},
        )

        self.assertEqual(list(response.context["station_rows"].object_list), [self.active_station])

    def test_same_station_name_is_allowed_for_different_platforms(self):
        platform_a = Platform.objects.create(name="Platform A", code="platform-a")
        platform_b = Platform.objects.create(name="Platform B", code="platform-b")

        first = Station.objects.create(
            platform=platform_a,
            branch=self.branch_one,
            organization=self.organization_one,
            name="Shared station",
        )
        second = Station.objects.create(
            platform=platform_b,
            branch=self.branch_one,
            organization=self.organization_one,
            name="Shared station",
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Station.objects.filter(name="Shared station").count(), 2)

    def test_position_organization_filter(self):
        response = self.client.get(
            reverse("settings_section", kwargs={"section": "positions"}),
            {"position_organization": self.organization_two.pk},
        )

        self.assertEqual(list(response.context["position_rows"].object_list), [self.south_position])

    def test_position_list_is_paginated(self):
        Position.objects.bulk_create([
            Position(
                branch=self.branch_one,
                organization=self.organization_one,
                name=f"Position {number:02d}",
            )
            for number in range(39)
        ])

        response = self.client.get(reverse("settings_section", kwargs={"section": "positions"}))

        page = response.context["position_rows"]
        self.assertEqual(page.paginator.count, 41)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(len(page.object_list), 40)

    def test_bulk_station_status_change_updates_selected_rows_only(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "stations"}),
            {
                "section": "station_bulk",
                "action": "bulk_deactivate",
                "selected_ids": [self.active_station.pk],
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "stations"}))
        self.active_station.refresh_from_db()
        self.inactive_station.refresh_from_db()
        self.assertFalse(self.active_station.is_active)
        self.assertFalse(self.inactive_station.is_active)

    def test_bulk_delete_removes_only_selected_stations(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "stations"}),
            {
                "section": "station_bulk",
                "action": "bulk_delete",
                "selected_ids": [self.active_station.pk],
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "stations"}))
        self.assertFalse(Station.objects.filter(pk=self.active_station.pk).exists())
        self.assertTrue(Station.objects.filter(pk=self.inactive_station.pk).exists())

    def test_bulk_delete_removes_selected_positions(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "positions"}),
            {
                "section": "position_bulk",
                "action": "bulk_delete",
                "selected_ids": [self.north_position.pk, self.south_position.pk],
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "positions"}))
        self.assertFalse(Position.objects.filter(pk__in=[self.north_position.pk, self.south_position.pk]).exists())

    def test_bulk_position_move_updates_branch_and_organization(self):
        platform = Platform.objects.create(name="Destination platform", code="destination-platform")
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "positions"}),
            {
                "section": "position_bulk",
                "action": "bulk_move",
                "selected_ids": [self.north_position.pk],
                "bulk_platform": platform.pk,
                "bulk_branch": self.branch_two.pk,
                "bulk_organization": self.organization_two.pk,
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "positions"}))
        self.north_position.refresh_from_db()
        self.assertEqual(self.north_position.organization, self.organization_two)
        self.assertEqual(self.north_position.branch, self.branch_two)
        self.assertEqual(self.north_position.platform, platform)

    def test_bulk_move_without_organization_is_validated(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "positions"}),
            {
                "section": "position_bulk",
                "action": "bulk_move",
                "selected_ids": [self.north_position.pk],
                "bulk_organization": "",
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "positions"}))
        self.north_position.refresh_from_db()
        self.assertEqual(self.north_position.organization, self.organization_one)

    def test_branch_manager_cannot_bulk_move_to_another_branch(self):
        platform = Platform.objects.create(name="Restricted platform", code="restricted-platform")
        branch_role = SiteRole.objects.create(name="Branch manager", code="branch_manager")
        branch_manager = User.objects.create_user("directory-branch-manager", password="test-password")
        profile = UserProfile.objects.create(user=branch_manager, branch=self.branch_one.name)
        profile.roles.add(branch_role)
        self.client.force_login(branch_manager)

        response = self.client.post(
            reverse("settings_section", kwargs={"section": "positions"}),
            {
                "section": "position_bulk",
                "action": "bulk_move",
                "selected_ids": [self.north_position.pk],
                "bulk_platform": platform.pk,
                "bulk_branch": self.branch_two.pk,
                "bulk_organization": self.organization_two.pk,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.north_position.refresh_from_db()
        self.assertEqual(self.north_position.organization, self.organization_one)

    def test_compact_directory_controls_are_rendered(self):
        station_response = self.client.get(reverse("settings_section", kwargs={"section": "stations"}))
        position_response = self.client.get(reverse("settings_section", kwargs={"section": "positions"}))

        self.assertContains(station_response, 'id="station-bulk-form"')
        self.assertContains(station_response, 'id="station-edit-dialog"')
        self.assertContains(position_response, 'id="position-bulk-form"')
        self.assertContains(position_response, 'id="position-edit-dialog"')
        self.assertContains(station_response, 'data-directory-bulk-delete')
        self.assertContains(position_response, 'data-directory-bulk-delete')

    def test_manager_account_types_are_hidden_from_editable_roles(self):
        SiteRole.objects.create(name="Branch manager", code="branch_manager")
        SiteRole.objects.create(name="Organization manager", code="organization_manager")
        ordinary_role = SiteRole.objects.create(name="Operator", code="operator")

        response = self.client.get(reverse("settings_section", kwargs={"section": "roles"}))

        visible_roles = response.context["roles"]
        self.assertIn(ordinary_role, visible_roles)
        self.assertFalse(visible_roles.filter(code__in=["branch_manager", "organization_manager"]).exists())

    def test_modal_record_id_updates_existing_station(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "stations"}),
            {
                "section": "station",
                "action": "save",
                "record_id": self.active_station.pk,
                "branch": self.branch_one.pk,
                "organization": self.organization_one.pk,
                "name": "Renamed enterprise",
                "sort_order": 7,
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "stations"}))
        self.active_station.refresh_from_db()
        self.assertEqual(self.active_station.name, "Renamed enterprise")
        self.assertEqual(self.active_station.sort_order, 7)


class DirectoryRoleVisibilityTests(TestCase):
    def setUp(self):
        self.platform_a = Platform.objects.create(name="Platform A", code="platform-a")
        self.platform_b = Platform.objects.create(name="Platform B", code="platform-b")
        self.branch_a = Branch.objects.create(name="Branch A", code="branch-a")
        self.branch_b = Branch.objects.create(name="Branch B", code="branch-b")
        self.organization_a = Organization.objects.create(
            branch=self.branch_a, name="Organization A", code="organization-a"
        )
        self.organization_b = Organization.objects.create(
            branch=self.branch_b, name="Organization B", code="organization-b"
        )
        self.station_platform_a = Station.objects.create(
            platform=self.platform_a,
            branch=self.branch_a,
            organization=self.organization_a,
            name="Shared name",
        )
        self.station_platform_b = Station.objects.create(
            platform=self.platform_b,
            branch=self.branch_a,
            organization=self.organization_a,
            name="Shared name",
        )
        self.station_scope_b = Station.objects.create(
            platform=self.platform_b,
            branch=self.branch_b,
            organization=self.organization_b,
            name="Shared name",
        )
        self.branch_role = SiteRole.objects.create(name="Branch manager", code="branch_manager")
        self.organization_role = SiteRole.objects.create(name="Organization manager", code="organization_manager")

    def _manager(self, username, role, branch, organization=""):
        user = User.objects.create_user(username, password="test-password")
        profile = UserProfile.objects.create(user=user, branch=branch, organization=organization)
        profile.roles.add(role)
        return user

    def _visible_station_ids(self, user):
        self.client.force_login(user)
        response = self.client.get(reverse("react_directory_api", kwargs={"section": "stations"}))
        self.assertEqual(response.status_code, 200)
        return {row["id"] for row in response.json()["rows"]}

    def test_every_role_sees_only_its_directory_scope(self):
        admin = User.objects.create_superuser("visibility-admin", password="test-password")
        branch_a_manager = self._manager("branch-a-manager", self.branch_role, self.branch_a.name)
        branch_b_manager = self._manager("branch-b-manager", self.branch_role, self.branch_b.name)
        organization_a_manager = self._manager(
            "organization-a-manager", self.organization_role, self.branch_a.name, self.organization_a.name
        )
        organization_b_manager = self._manager(
            "organization-b-manager", self.organization_role, self.branch_b.name, self.organization_b.name
        )

        first_two = {self.station_platform_a.id, self.station_platform_b.id}
        last_one = {self.station_scope_b.id}
        self.assertEqual(self._visible_station_ids(admin), first_two | last_one)
        self.assertEqual(self._visible_station_ids(branch_a_manager), first_two)
        self.assertEqual(self._visible_station_ids(branch_b_manager), last_one)
        self.assertEqual(self._visible_station_ids(organization_a_manager), first_two)
        self.assertEqual(self._visible_station_ids(organization_b_manager), last_one)

    def test_regular_user_only_receives_assigned_station(self):
        user = User.objects.create_user("limited-user", password="test-password")
        profile = UserProfile.objects.create(user=user)
        profile.allowed_platforms.add(self.platform_a)
        profile.allowed_stations.add(self.station_platform_a)
        self.client.force_login(user)

        response = self.client.get(reverse("public_stations_api"), {"platform": self.platform_a.name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["results"]], [self.station_platform_a.id])

    def test_public_directory_is_filtered_by_selected_platform(self):
        response = self.client.get(reverse("public_stations_api"), {"platform": self.platform_b.name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.json()["results"]},
            {self.station_platform_b.id, self.station_scope_b.id},
        )

    def test_custom_admin_role_like_akt_sees_every_scope_and_has_full_admin_access(self):
        akt_role = SiteRole.objects.create(
            name="AKT",
            code="akt",
            is_admin_role=True,
            can_directories=True,
            can_api_settings=False,
            can_site_settings=False,
        )
        akt_user = User.objects.create_user("akt-user", password="test-password")
        profile = UserProfile.objects.create(
            user=akt_user,
            branch=self.branch_a.name,
            organization=self.organization_a.name,
        )
        profile.roles.add(akt_role)

        self.assertEqual(
            self._visible_station_ids(akt_user),
            {self.station_platform_a.id, self.station_platform_b.id, self.station_scope_b.id},
        )
        self.assertTrue(user_can_api_settings(akt_user))
        self.assertTrue(user_can_site_settings(akt_user))

    def test_non_admin_custom_role_only_sees_explicitly_assigned_directories(self):
        staff_role = SiteRole.objects.create(
            name="Scoped AKT",
            code="scoped-akt",
            is_staff_role=True,
            can_directories=True,
        )
        user = User.objects.create_user("scoped-akt-user", password="test-password")
        profile = UserProfile.objects.create(user=user)
        profile.roles.add(staff_role)
        profile.allowed_platforms.add(self.platform_a)
        profile.allowed_stations.add(self.station_platform_a)

        self.assertEqual(self._visible_station_ids(user), {self.station_platform_a.id})
