import json
import uuid

from django.test import TestCase
from django.urls import reverse


class PublicDocumentViewerTests(TestCase):
    def test_document_page_is_available_without_authentication(self):
        response = self.client.get("/document/%D0%90%D1%85%D0%B1%D0%BE%D1%80%D0%BE%D1%82%20%D1%85%D0%B0%D0%B2%D1%84%D1%81%D0%B8%D0%B7%D0%BB%D0%B8%D0%B3%D0%B8%20%D1%81%D0%B8%D1%91%D1%81%D0%B0%D1%82%D0%B8/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ахборот хавфсизлиги сиёсати")
        self.assertContains(response, "/static/documents/security-policy/policy-2026.docx")

    def test_anonymous_view_and_download_update_public_statistics(self):
        event_url = reverse("public_document_event_api", args=["security-policy"])
        visitor_id = str(uuid.uuid4())
        for kind in ("view", "download"):
            response = self.client.post(
                event_url,
                data=json.dumps({"kind": kind, "visitor_id": visitor_id, "event_id": str(uuid.uuid4())}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)

        stats = self.client.get(reverse("public_document_stats_api", args=["security-policy"])).json()
        self.assertEqual(stats, {"views": 1, "visitors": 1, "downloads": 1, "online": 1})
