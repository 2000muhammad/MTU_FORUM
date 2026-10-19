from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.directory_localization import localize_directory_name
from core.models import Platform, Position, SiteRole, Station, UserProfile


class DirectoryLocalizationTests(TestCase):
    def test_known_positions_and_station_names_are_localized(self):
        self.assertEqual(localize_directory_name("Начальник станции", "uz"), "Stansiya boshlig‘i")
        self.assertEqual(localize_directory_name("Начальник станции", "en"), "Station chief")
        self.assertEqual(localize_directory_name("Станция Салар", "uz"), "Salar stansiyasi")
        self.assertEqual(localize_directory_name("Станция Салар", "en"), "Salar Station")
        self.assertEqual(localize_directory_name("Станция Салар", "ru"), "Станция Салар")

    def test_public_api_returns_translated_label_and_original_value(self):
        platform = Platform.objects.create(name='"Единое окно" АО «Ўзбекистон темир йўллари»')
        station = Station.objects.create(platform=platform, name="Станция Салар")

        response = self.client.get(reverse("public_stations_api"), {"platform": platform.name, "lang": "en"})

        self.assertEqual(response.status_code, 200)
        row = response.json()["results"][0]
        self.assertEqual(row["name"], station.name)
        self.assertEqual(row["label"], "Salar Station")

    def test_react_directory_uses_display_name_without_changing_edit_value(self):
        role = SiteRole.objects.create(name="Directory editor", code="directory-editor", can_directories=True)
        user = User.objects.create_user("directory-translator", password="test-password")
        profile = UserProfile.objects.create(user=user)
        profile.roles.add(role)
        position = Position.objects.create(name="Начальник станции")
        profile.allowed_positions.add(position)
        self.client.force_login(user)

        response = self.client.get(
            reverse("react_directory_api", kwargs={"section": "positions"}),
            {"lang": "uz"},
        )

        self.assertEqual(response.status_code, 200)
        row = response.json()["rows"][0]
        self.assertEqual(row["name"], "Начальник станции")
        self.assertEqual(row["display_name"], "Stansiya boshlig‘i")
