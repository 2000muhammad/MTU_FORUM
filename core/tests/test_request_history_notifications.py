from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import IntakeRequest, IntakeRequestHistory


class RequestHistoryNotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("history-admin", password="test-password")
        self.client.force_login(self.admin)
        self.item = IntakeRequest.objects.create(
            pnfl="12345678901234",
            full_name="Test User",
            company="Station",
            position="Operator",
            passport="AA1234567",
            phone="+998901234567",
            telegram_id=778899,
            platform="Platform",
            cause="Test",
            lang="ru",
        )

    def payload(self, **overrides):
        data = {
            "action": "save",
            "pnfl": self.item.pnfl,
            "full_name": self.item.full_name,
            "company": self.item.company,
            "department": self.item.department,
            "position": self.item.position,
            "passport": self.item.passport,
            "phone": self.item.phone,
            "telegram_id": self.item.telegram_id,
            "platform": self.item.platform,
            "cause": self.item.cause,
            "status": IntakeRequest.Status.DONE,
        }
        data.update(overrides)
        return data

    @patch("core.views.send_telegram_message", return_value={"ok": True})
    def test_status_change_is_recorded_and_notified(self, send_message):
        response = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(),
        )

        self.assertRedirects(response, reverse("requests"))
        entry = IntakeRequestHistory.objects.get(request=self.item)
        self.assertEqual(entry.event, IntakeRequestHistory.Event.STATUS)
        self.assertEqual(entry.from_status, IntakeRequest.Status.NEW)
        self.assertEqual(entry.to_status, IntakeRequest.Status.DONE)
        self.assertTrue(entry.telegram_notified)
        self.assertEqual(entry.actor, self.admin)
        send_message.assert_called_once()
        self.assertIn("#", send_message.call_args.args[1])

    @patch("core.views.send_telegram_message", side_effect=RuntimeError("Telegram unavailable"))
    def test_notification_failure_does_not_cancel_status_change(self, _send_message):
        response = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(status=IntakeRequest.Status.BLOCKED),
        )

        self.assertRedirects(response, reverse("requests"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, IntakeRequest.Status.BLOCKED)
        entry = IntakeRequestHistory.objects.get(request=self.item)
        self.assertFalse(entry.telegram_notified)
        self.assertIn("Telegram unavailable", entry.telegram_error)

