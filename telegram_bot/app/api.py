import requests
from .config import SITE_API_KEY, SITE_BASE_URL

HEADERS = {"X-API-KEY": SITE_API_KEY}


def _get_results(path):
    try:
        return requests.get(f"{SITE_BASE_URL}{path}", timeout=15).json().get("results", [])
    except requests.RequestException:
        return []
    except ValueError:
        return []


def get_stations():
    return _get_results("/api/public/stations/")


def get_positions():
    return _get_results("/api/public/positions/")


def get_platforms():
    return _get_results("/api/public/platforms/")


def get_channels():
    return _get_results("/api/public/subscription-channels/")


def submit_request(payload):
    try:
        response = requests.post(f"{SITE_BASE_URL}/api/intake/telegram/", json=payload, headers=HEADERS, timeout=20)
        data = response.json()
    except requests.RequestException as exc:
        return {"ok": False, "message": str(exc)}
    except ValueError:
        return {"ok": False, "message": "Invalid response from site API."}
    if response.status_code >= 400:
        data.setdefault("ok", False)
    return data


def send_chat_message(payload):
    return requests.post(f"{SITE_BASE_URL}/api/chat/incoming/", json=payload, headers=HEADERS, timeout=15).json()


def send_chat_media(payload, file_obj=None, filename=""):
    files = {"attachment": (filename, file_obj)} if file_obj else None
    response = requests.post(
        f"{SITE_BASE_URL}/api/chat/incoming/",
        data=payload,
        files=files,
        headers=HEADERS,
        timeout=30,
    )
    return response.json()


def get_chat_threads(telegram_id):
    try:
        return requests.get(
            f"{SITE_BASE_URL}/api/chat/threads/",
            params={"telegram_id": telegram_id},
            headers=HEADERS,
            timeout=15,
        ).json().get("threads", [])
    except (requests.RequestException, ValueError):
        return []


def create_chat_thread(telegram_id, full_name=""):
    try:
        return requests.post(
            f"{SITE_BASE_URL}/api/chat/threads/",
            data={"action": "create", "telegram_id": telegram_id, "full_name": full_name},
            headers=HEADERS,
            timeout=15,
        ).json()
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "message": str(exc)}


def close_chat_thread(telegram_id, thread_id):
    try:
        return requests.post(
            f"{SITE_BASE_URL}/api/chat/threads/",
            data={"action": "close", "telegram_id": telegram_id, "thread_id": thread_id},
            headers=HEADERS,
            timeout=15,
        ).json()
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "message": str(exc)}


def get_intake_summary(telegram_id):
    try:
        return requests.get(
            f"{SITE_BASE_URL}/api/intake/telegram/summary/",
            params={"telegram_id": telegram_id},
            headers=HEADERS,
            timeout=15,
        ).json()
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "message": str(exc)}
