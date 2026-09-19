from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Branch, Organization, Position, SiteRole, Station, UserProfile


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

    def test_bulk_position_move_updates_branch_and_organization(self):
        response = self.client.post(
            reverse("settings_section", kwargs={"section": "positions"}),
            {
                "section": "position_bulk",
                "action": "bulk_move",
                "selected_ids": [self.north_position.pk],
                "bulk_organization": self.organization_two.pk,
            },
        )

        self.assertRedirects(response, reverse("settings_section", kwargs={"section": "positions"}))
        self.north_position.refresh_from_db()
        self.assertEqual(self.north_position.organization, self.organization_two)
        self.assertEqual(self.north_position.branch, self.branch_two)

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
