import json
import uuid

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import PublicDocument


class PublicDocumentViewerTests(TestCase):
    def test_superuser_can_import_text_document(self):
        admin = User.objects.create_superuser("doc-admin", password="Strong-pass-123")
        self.client.force_login(admin)

        response = self.client.post(
            reverse("public_document_import"),
            {
                "title": "Регламент отдела",
                "slug": "reglament",
                "document": SimpleUploadedFile("reglament.txt", "Первый раздел\nВторой раздел".encode(), content_type="text/plain"),
            },
        )

        document = PublicDocument.objects.get(slug="reglament")
        self.assertRedirects(response, reverse("public_document_short", args=["reglament"]))
        self.assertIn("Первый раздел", document.content_html)
        self.assertContains(self.client.get(reverse("public_document_short", args=["reglament"])), "Регламент отдела")

    def test_regular_user_cannot_import_document(self):
        user = User.objects.create_user("employee", password="Strong-pass-123")
        self.client.force_login(user)

        response = self.client.post(reverse("public_document_import"))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(PublicDocument.objects.exists())

    def test_document_has_short_canonical_address(self):
        response = self.client.get(reverse("public_document_root"))

        self.assertEqual(reverse("public_document_root"), "/document/ax")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ахборот хавфсизлиги сиёсати")

    def test_embedded_document_navigation_keeps_embedded_mode(self):
        PublicDocument.objects.create(
            title="Инструкция",
            slug="instruction",
            source_file=SimpleUploadedFile("instruction.txt", b"Text"),
            file_type="txt",
            content_html="<p>Text</p>",
        )

        response = self.client.get(reverse("public_document_root"), {"embedded": "1"})

        self.assertContains(response, "/document/ax?embedded=1")
        self.assertContains(response, "/document/instruction?embedded=1")

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
