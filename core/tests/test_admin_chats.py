from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import AdminChatThread, UserProfile


class AdminChatCreationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("chat-admin", password="test-password")
        self.client.force_login(self.admin)

    def test_chat_can_be_created_from_telegram_id(self):
        response = self.client.post(reverse("admin_chat_list"), {
            "telegram_identity": "778899",
            "full_name": "Telegram User",
        })
        thread = AdminChatThread.objects.get()
        self.assertRedirects(response, reverse("admin_chat_thread_detail", args=[thread.pk]))
        self.assertEqual(thread.telegram_id, 778899)

    def test_chat_can_be_created_from_known_nickname(self):
        user = User.objects.create_user("known-user", first_name="Known", last_name="User")
        UserProfile.objects.create(user=user, telegram_id=991122, telegram_username="known_nick")
        response = self.client.post(reverse("admin_chat_list"), {"telegram_identity": "@KNOWN_NICK"})
        thread = AdminChatThread.objects.get()
        self.assertRedirects(response, reverse("admin_chat_thread_detail", args=[thread.pk]))
        self.assertEqual(thread.telegram_id, 991122)
        self.assertEqual(thread.telegram_username, "known_nick")
        self.assertEqual(thread.full_name, "Known User")

    def test_unknown_nickname_shows_error_without_creating_chat(self):
        response = self.client.post(reverse("admin_chat_list"), {"telegram_identity": "@unknown_nick"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пользователь не найден")
        self.assertFalse(AdminChatThread.objects.exists())
