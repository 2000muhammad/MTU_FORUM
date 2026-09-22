import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import requests
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils import timezone

from core.models import ApiConfiguration, ExternalApiConnection, SiteLog, WebPlatform
from core.site_logs import write_site_log


class Command(BaseCommand):
    help = "Create a database backup and check Telegram/external integrations."

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
        target = backup_dir / f"mtu-forum-{stamp}.json"
        temporary = target.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as output:
            call_command(
                "dumpdata",
                exclude=["contenttypes", "auth.permission", "sessions"],
                indent=2,
                stdout=output,
            )
        temporary.replace(target)

        cutoff = timezone.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
        for old_file in backup_dir.glob("mtu-forum-*.json"):
            if timezone.datetime.fromtimestamp(old_file.stat().st_mtime, tz=timezone.get_current_timezone()) < cutoff:
                old_file.unlink(missing_ok=True)
        write_site_log(source="maintenance", action="automatic_backup", message=f"Backup created: {target.name}")

        config = ApiConfiguration.load()
        token = config.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
        telegram_ok = False
        if token:
            try:
                telegram_ok = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).ok
            except requests.RequestException:
                telegram_ok = False
        write_site_log(
            level=SiteLog.Level.INFO if telegram_ok else SiteLog.Level.ERROR,
            source="maintenance",
            action="telegram_health",
            message="Telegram bot is available." if telegram_ok else "Telegram bot is unavailable.",
        )

        for connection in ExternalApiConnection.objects.filter(is_active=True):
            try:
                response = requests.get(connection.test_url, timeout=max(3, connection.timeout_seconds))
                connection.last_status_code = response.status_code
                connection.last_error = "" if response.ok else f"HTTP {response.status_code}"
            except requests.RequestException as exc:
                connection.last_status_code = None
                connection.last_error = str(exc)[:500]
            connection.last_checked_at = timezone.now()
            connection.save(update_fields=["last_status_code", "last_error", "last_checked_at", "updated_at"])
        platforms = list(WebPlatform.objects.filter(is_active=True).exclude(url=""))

        def check_platform(platform):
            try:
                response = requests.get(platform.url, timeout=10, allow_redirects=True)
                return platform, response.status_code < 500, response.status_code
            except requests.RequestException:
                return platform, False, None

        with ThreadPoolExecutor(max_workers=min(8, max(1, len(platforms)))) as pool:
            platform_results = list(pool.map(check_platform, platforms))
        for platform, ok, status_code in platform_results:
            write_site_log(
                level=SiteLog.Level.INFO if ok else SiteLog.Level.ERROR,
                source="maintenance",
                action="web_platform_health",
                message=f"{platform.name}: {'available' if ok else 'unavailable'}",
                status_code=status_code,
                meta={"platform_id": platform.pk, "url": platform.url},
            )
        self.stdout.write(self.style.SUCCESS(json.dumps({"backup": target.name, "telegram": telegram_ok})))
