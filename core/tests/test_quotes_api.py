from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import ExternalApiConnection


class QuotesApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quote-user", password="secret")
        self.client.force_login(self.user)
        self.connection = ExternalApiConnection.objects.create(
            name="API Ninjas Quotes",
            base_url="https://api.api-ninjas.com/v2/randomquotes",
            method="GET",
            auth_header="X-Api-Key",
            api_key="test-key",
            timeout_seconds=8,
        )

    @override_settings(API_NINJAS_API_KEY="")
    @patch("core.views.requests.get")
    def test_returns_english_quote_from_api_ninjas(self, request_get):
        response = Mock()
        response.json.return_value = [{"quote": "Wisdom begins in wonder.", "author": "Socrates"}]
        request_get.return_value = response

        result = self.client.get(reverse("react_quote_api"), {"lang": "en"})

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["quote"]["text"], "Wisdom begins in wonder.")
        self.assertEqual(request_get.call_args.kwargs["headers"], {"X-Api-Key": "test-key"})

    @override_settings(API_NINJAS_API_KEY="")
    @patch("core.views.requests.get")
    def test_localizes_non_english_quote(self, request_get):
        quote_response = Mock()
        quote_response.json.return_value = [{"quote": "Knowledge is power.", "author": "Francis Bacon"}]
        translated_quote = Mock()
        translated_quote.json.return_value = {"responseData": {"translatedText": "Знание &#39;—&#39; сила."}}
        translated_author = Mock()
        translated_author.json.return_value = {"responseData": {"translatedText": "Фрэнсис Бэкон"}}
        request_get.side_effect = [quote_response, translated_quote, translated_author]

        result = self.client.get(reverse("react_quote_api"), {"lang": "ru"})

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["quote"], {"text": "Знание '—' сила.", "author": "Фрэнсис Бэкон"})

    @override_settings(API_NINJAS_API_KEY="")
    def test_uses_local_fallback_when_key_is_missing(self):
        self.connection.api_key = ""
        self.connection.save(update_fields=["api_key"])

        result = self.client.get(reverse("react_quote_api"), {"lang": "uz"})

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {"ok": False, "configured": False, "fallback": True})
