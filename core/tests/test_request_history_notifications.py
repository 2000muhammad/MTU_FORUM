from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import IntakeRequest, IntakeRequestHistory, Platform, SiteRole, UserProfile


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

        self.assertRedirects(response, "/app/requests/")
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

        self.assertRedirects(response, "/app/requests/")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, IntakeRequest.Status.BLOCKED)
        entry = IntakeRequestHistory.objects.get(request=self.item)
        self.assertFalse(entry.telegram_notified)
        self.assertIn("Telegram unavailable", entry.telegram_error)

    def test_internal_notes_are_saved_and_recorded_in_history(self):
        note = "Проверить согласование доступа с руководителем."

        response = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(action="save_note", status=IntakeRequest.Status.NEW, internal_notes=note),
        )

        self.assertRedirects(response, reverse("request_edit", kwargs={"pk": self.item.pk}))
        self.item.refresh_from_db()
        self.assertEqual(self.item.internal_notes, note)
        entry = IntakeRequestHistory.objects.get(request=self.item)
        self.assertEqual(entry.event, IntakeRequestHistory.Event.UPDATED)
        self.assertEqual(entry.changes["Заметки"]["new"], note)

        editor = self.client.get(reverse("request_edit", kwargs={"pk": self.item.pk}))
        self.assertContains(editor, "Редактор заявки")
        self.assertContains(editor, "Только для сотрудников")
        self.assertContains(editor, 'id="id_internal_notes"')
        self.assertContains(editor, note)
        self.assertContains(editor, "Создана:")
        self.assertContains(editor, "Статус заявки")
        self.assertContains(editor, "После нажатия «Сохранить» статус автоматически изменится на «Сделано».")
        self.assertContains(editor, '<button type="button" data-copy-request-field>', count=9)
        self.assertContains(editor, '<button type="button" data-edit-request-field>', count=9)
        self.assertContains(editor, 'name="cause"')
        self.assertContains(editor, 'readonly="readonly"')

    @patch("core.views.send_telegram_message", return_value={"ok": True})
    def test_save_completes_request_and_keeps_original_cause(self, _send_message):
        response = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(cause="Изменённая причина"),
        )

        self.assertRedirects(response, "/app/requests/")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, IntakeRequest.Status.DONE)
        self.assertEqual(self.item.cause, "Test")

    @patch("core.views.send_telegram_message", return_value={"ok": True})
    def test_request_can_be_blocked_and_returned_to_new(self, send_message):
        blocked = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(action="block_request", status=IntakeRequest.Status.NEW),
        )

        self.assertRedirects(blocked, reverse("request_edit", kwargs={"pk": self.item.pk}))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, IntakeRequest.Status.BLOCKED)
        self.assertTrue(self.item.history.filter(to_status=IntakeRequest.Status.BLOCKED).exists())

        restored = self.client.post(
            reverse("request_edit", kwargs={"pk": self.item.pk}),
            self.payload(action="unblock_request", status=IntakeRequest.Status.BLOCKED),
        )

        self.assertRedirects(restored, reverse("request_edit", kwargs={"pk": self.item.pk}))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, IntakeRequest.Status.NEW)
        self.assertTrue(self.item.history.filter(to_status=IntakeRequest.Status.NEW).exists())
        self.assertEqual(send_message.call_count, 2)

    def test_request_is_assigned_to_least_loaded_operator_with_platform_access(self):
        platform = Platform.objects.create(name="Platform", code="platform")
        other_platform = Platform.objects.create(name="Other", code="other")
        role = SiteRole.objects.create(name="Оператор", code="operator", can_requests=True)

        busy = User.objects.create_user("busy")
        busy_profile = UserProfile.objects.create(user=busy)
        busy_profile.roles.add(role)
        busy_profile.allowed_platforms.add(platform)
        available = User.objects.create_user("available")
        available_profile = UserProfile.objects.create(user=available)
        available_profile.roles.add(role)
        available_profile.allowed_platforms.add(platform)
        excluded = User.objects.create_user("excluded")
        excluded_profile = UserProfile.objects.create(user=excluded)
        excluded_profile.roles.add(role)
        excluded_profile.allowed_platforms.add(other_platform)
        IntakeRequest.objects.create(pnfl="90000000000001", telegram_id=9001, platform=platform.name, assignee=busy)

        response = self.client.get(reverse("request_edit", kwargs={"pk": self.item.pk}))

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.assignee, available)
        assignment = self.item.history.get(event=IntakeRequestHistory.Event.ASSIGNMENT)
        self.assertEqual(assignment.changes["Исполнитель"]["new"], available.username)

