import requests
from django.conf import settings


def _telegram_error(response):
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]
    return payload.get("description") or str(payload)[:500]


def _post_telegram_file(token, endpoint, data, field_name, filename, file_obj, *, timeout=60):
    if file_obj and hasattr(file_obj, "seek"):
        file_obj.seek(0)
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{endpoint}",
        data=data,
        files={field_name: (filename or "upload", file_obj)},
        timeout=timeout,
    )
    if not response.ok:
        raise RuntimeError(f"{endpoint}: {_telegram_error(response)}")
    return response.json()


def _bot_token():
    from .models import ApiConfiguration

    return ApiConfiguration.load().telegram_bot_token or settings.TELEGRAM_BOT_TOKEN


def send_telegram_message(telegram_id, text, reply_markup=None):
    """Small Bot API wrapper used by the admin panel and intake endpoint."""
    token = _bot_token()
    if not token:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN is empty"}

    payload = {"chat_id": telegram_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def send_telegram_media(telegram_id, kind, *, file_obj=None, filename="", caption="", latitude=None, longitude=None):
    token = _bot_token()
    if not token:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN is empty"}

    if kind == "location":
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendLocation",
            data={"chat_id": telegram_id, "latitude": latitude, "longitude": longitude},
            timeout=15,
        )
        response.raise_for_status()
        if caption:
            send_telegram_message(telegram_id, caption)
        return response.json()

    endpoints = {
        "photo": ("sendPhoto", "photo"),
        "video": ("sendVideo", "video"),
        "document": ("sendDocument", "document"),
        "voice": ("sendVoice", "voice"),
        "video_note": ("sendVideoNote", "video_note"),
    }
    endpoint, field_name = endpoints[kind]
    data = {"chat_id": telegram_id}
    if caption and kind != "video_note":
        data["caption"] = caption
        data["parse_mode"] = "HTML"

    errors = []
    try:
        result = _post_telegram_file(token, endpoint, data, field_name, filename, file_obj)
        if caption and kind == "video_note":
            send_telegram_message(telegram_id, caption)
        return result
    except RuntimeError as exc:
        errors.append(str(exc))

    fallback_data = {"chat_id": telegram_id}
    if caption:
        fallback_data["caption"] = caption
        fallback_data["parse_mode"] = "HTML"

    fallback_chain = []
    if kind == "voice":
        fallback_chain = [("sendAudio", "audio"), ("sendDocument", "document")]
    elif kind == "video":
        fallback_chain = [("sendDocument", "document")]
    elif kind == "video_note":
        fallback_chain = [("sendVideo", "video"), ("sendDocument", "document")]

    for fallback_endpoint, fallback_field in fallback_chain:
        try:
            return _post_telegram_file(token, fallback_endpoint, fallback_data, fallback_field, filename or "upload.webm", file_obj)
        except RuntimeError as exc:
            errors.append(str(exc))

    raise RuntimeError("; ".join(errors))


def get_telegram_profile_photo(telegram_id):
    """Return (bytes, content_type) for the latest Telegram profile photo."""
    token = _bot_token()
    if not token:
        return None

    try:
        photos_response = requests.get(
            f"https://api.telegram.org/bot{token}/getUserProfilePhotos",
            params={"user_id": telegram_id, "limit": 1},
            timeout=12,
        )
        photos_response.raise_for_status()
        photos = photos_response.json().get("result", {}).get("photos", [])
        if not photos:
            return None

        file_id = photos[0][-1]["file_id"]
        file_response = requests.get(
            f"https://api.telegram.org/bot{token}/getFile",
            params={"file_id": file_id},
            timeout=12,
        )
        file_response.raise_for_status()
        file_path = file_response.json().get("result", {}).get("file_path")
        if not file_path:
            return None

        image_response = requests.get(f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=15)
        image_response.raise_for_status()
        content_type = image_response.headers.get("Content-Type", "image/jpeg")
        return image_response.content, content_type
    except requests.RequestException:
        return None
