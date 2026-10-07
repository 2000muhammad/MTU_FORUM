import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import ApiConfiguration, IntakeRequest


class TelegramIntakeTests(TestCase):
    def setUp(self):
        config = ApiConfiguration.load()
        config.telegram_api_key = "test-telegram-api-key"
        config.save(update_fields=["telegram_api_key"])

    @patch("core.hrm_client.HRMClient.find_employee")
    def test_request_is_saved_without_hrm_lookup(self, find_employee):
        response = self.client.post(
            reverse("telegram_intake_api"),
            data=json.dumps(
                {
                    "pnfl": "12345678901234",
                    "telegram_id": 998001234567,
                    "full_name": "Test Employee",
                    "phone": "+998-90-123-45-67",
                    "company": "Test station",
                    "station": "Test station",
                    "department": "Digitalization department",
                    "selected_position": "Operator",
                    "passport": "AA1234567",
                    "lang": "uz",
                    "cause": "Account access",
                    "platform": "MTU FORUM",
                    "reply_via_bot": True,
                }
            ),
            content_type="application/json",
            HTTP_X_API_KEY="test-telegram-api-key",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertNotIn("hrm_found", response.json())
        self.assertNotIn("hrm_disabled", response.json())
        find_employee.assert_not_called()

        request = IntakeRequest.objects.get(telegram_id=998001234567)
        self.assertEqual(request.pnfl, "12345678901234")
        self.assertEqual(request.phone, "+998-90-123-45-67")
        self.assertEqual(request.full_name, "Test Employee")
        self.assertEqual(request.passport, "AA1234567")
        self.assertEqual(request.company, "Test station")
        self.assertEqual(request.station, "Test station")
        self.assertEqual(request.department, "Digitalization department")
        self.assertEqual(request.position, "Operator")
        self.assertEqual(request.lang, "uz")
        self.assertEqual(request.cause, "Account access")
        self.assertEqual(request.platform, "MTU FORUM")
        self.assertEqual(request.status, IntakeRequest.Status.NEW)
        self.assertEqual(request.hrm_payload, {})
