import time

from django.core.management.base import BaseCommand

from core.password_policy import send_due_password_reminders


class Command(BaseCommand):
    help = "Send one Telegram reminder per day to users with temporary passwords."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=int, default=3600)

    def handle(self, *args, **options):
        while True:
            sent = send_due_password_reminders()
            if sent:
                self.stdout.write(self.style.SUCCESS(f"Password reminders sent: {sent}"))
            if options["once"]:
                return
            time.sleep(max(60, options["interval"]))
