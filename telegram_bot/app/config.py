import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")
SITE_API_KEY = os.getenv("TELEGRAM_API_KEY", "change-me-api-key")
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru")
