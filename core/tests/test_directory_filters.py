import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Branch, Organization, Position, Station


class DirectoryApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("directory-admin", password="test-password")
        self.client.force_login(self.admin)
        self.branch_one = Branch.objects.create(name="North branch", code="north")
        self.branch_two = Branch.objects.create(name="South branch", code="south")
        self.organization_one = Organization.objects.create(branch=self.branch_one, name="North organization", code="north-org")
        self.organization_two = Organization.objects.create(branch=self.branch_two, name="South organization", code="south-org")
        self.active_station = Station.objects.create(branch=self.branch_one, organization=self.organization_one, name="Central enterprise", code="central-enterprise")
        self.inactive_station = Station.objects.create(branch=self.branch_two, organization=self.organization_two, name="Remote enterprise", code="remote-enterprise", is_active=False)
        self.north_position = Position.objects.create(branch=self.branch_one, organization=self.organization_one, name="North engineer")

    def endpoint(self, section):
        return reverse("react_directory_api", kwargs={"section": section})

    def post(self, section, payload):
        return self.client.post(self.endpoint(section), data=json.dumps(payload), content_type="application/json")

    def test_api_returns_directory_rows_and_filter_metadata(self):
        response = self.client.get(self.endpoint("stations"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual({row["id"] for row in payload["rows"]}, {self.active_station.id, self.inactive_station.id})
        self.assertEqual({row["id"] for row in payload["branches"]}, {self.branch_one.id, self.branch_two.id})

    def test_bulk_station_status_change_updates_selected_rows_only(self):
        response = self.post("stations", {"action": "bulk_deactivate", "selected_ids": [self.active_station.pk]})
        self.assertEqual(response.status_code, 200)
        self.active_station.refresh_from_db()
        self.inactive_station.refresh_from_db()
        self.assertFalse(self.active_station.is_active)
        self.assertFalse(self.inactive_station.is_active)

    def test_record_id_updates_existing_station(self):
        response = self.post("stations", {
            "record_id": self.active_station.pk,
            "branch": self.branch_one.pk,
            "organization": self.organization_one.pk,
            "name": "Renamed enterprise",
            "sort_order": 7,
            "is_active": True,
        })
        self.assertEqual(response.status_code, 200)
        self.active_station.refresh_from_db()
        self.assertEqual(self.active_station.name, "Renamed enterprise")
        self.assertEqual(self.active_station.sort_order, 7)

    def test_api_creates_position(self):
        response = self.post("positions", {
            "branch": self.branch_two.pk,
            "organization": self.organization_two.pk,
            "name": "New position",
            "sort_order": 2,
            "is_active": True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Position.objects.filter(name="New position", organization=self.organization_two).exists())
