import json
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import TelegramAccountLink, UserProfile


@override_settings(TELEGRAM_BOT_USERNAME="mtu_test_bot", TELEGRAM_API_KEY="test-key")
class TelegramProfileLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("linked-user", password="old-password")
        self.profile = UserProfile.objects.create(user=self.user, phone="+998-90-123-45-67")
        self.client.force_login(self.user)

    def _start_link(self):
        response = self.client.get(reverse("telegram_profile_link"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).netloc, "t.me")
        start = parse_qs(urlparse(response.url).query)["start"][0]
        self.assertTrue(start.startswith("bind_"))
        return start.removeprefix("bind_")

    def test_contact_number_must_match_profile(self):
        token = self._start_link()
        response = self.client.post(
            reverse("telegram_profile_link_complete_api"),
            data=json.dumps({
                "token": token,
                "telegram_id": 777,
                "username": "telegram_user",
                "phone": "+998901111111",
            }),
            content_type="application/json",
            HTTP_X_API_KEY="test-key",
        )
        self.assertEqual(response.status_code, 400)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.telegram_verified_at)

    def test_verified_contact_links_profile_and_can_be_unlinked(self):
        token = self._start_link()
        response = self.client.post(
            reverse("telegram_profile_link_complete_api"),
            data=json.dumps({
                "token": token,
                "telegram_id": 777,
                "username": "telegram_user",
                "phone": "998901234567",
            }),
            content_type="application/json",
            HTTP_X_API_KEY="test-key",
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.telegram_id, 777)
        self.assertEqual(self.profile.telegram_username, "telegram_user")
        self.assertIsNotNone(self.profile.telegram_verified_at)
        self.assertEqual(TelegramAccountLink.objects.filter(used_at__isnull=False).count(), 1)

        unlink = self.client.post(reverse("profile"), {"action": "telegram_unlink"})
        self.assertEqual(unlink.status_code, 302)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.telegram_id)
        self.assertIsNone(self.profile.telegram_verified_at)
