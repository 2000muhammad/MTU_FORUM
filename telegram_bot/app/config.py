import os
from pathlib import Path

from dotenv import load_dotenv


# Production services may start inside the telegram_bot directory. Always load
# the shared project settings from the repository root, regardless of cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SITE_BASE_URL = os.getenv(
    "SITE_BASE_URL", "https://forum.mtutoshkent.uz"
).strip().rstrip("/")
SITE_API_KEY = os.getenv("TELEGRAM_API_KEY", "change-me-api-key").strip()
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru").strip() or "ru"
