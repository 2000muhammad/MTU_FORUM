from io import BytesIO
from pathlib import Path
import re

from app import states
from app.api import (
    close_chat_thread,
    create_chat_thread,
    get_chat_threads,
    get_intake_summary,
    get_platforms,
    get_positions,
    get_stations,
    send_chat_media,
    send_chat_message,
    submit_request,
)
from app.keyboards import (
    LANGUAGE_CODES,
    active_chat_keyboard,
    all_menu_labels,
    back_keyboard,
    back_label,
    chat_select_keyboard,
    choice_keyboard,
    close_chat_label,
    contact_keyboard,
    language_keyboard,
    main_menu,
    new_chat_label,
    subscription_keyboard,
)
from app.subscription import missing_channels
from app.texts import t


PINFL_HINT_IMAGE = Path(__file__).resolve().parents[2] / "assets" / "pinfl_hint.jpg"


def _menu_action(text):
    return all_menu_labels().get(text)


def _matches_label(text, label_func, lang):
    if text == label_func(lang):
        return True
    return any(text == label_func(code) for code in LANGUAGE_CODES)


def _is_back(text, lang):
    return _matches_label(text, back_label, lang)


def _is_close_chat(text, lang):
    return _matches_label(text, close_chat_label, lang)


def _is_new_chat(text, lang):
    return _matches_label(text, new_chat_label, lang)


def _normalize_passport(value):
    passport = re.sub(r"\s+", "", value or "").upper()
    return passport if re.fullmatch(r"[A-Z]{2}\d{7}", passport) else ""


def _normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 9:
        digits = f"998{digits}"
    if len(digits) != 12 or not digits.startswith("998"):
        return ""
    return f"+998-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"


def _choices_markup(items, lang):
    return choice_keyboard(items, lang, include_back=True) if items else back_keyboard(lang)


def _thread_button_label(item):
    title = item.get("title") or f"Chat #{item.get('id')}"
    return f"{title} · #{item.get('id')}"


def _format_request_row(row):
    head = " | ".join(part for part in [
        f"#{row.get('id')}" if row.get("id") else "",
        row.get("date", ""),
        row.get("platform", ""),
        row.get("status", ""),
    ] if part)
    details = []
    if row.get("full_name"):
        details.append(row["full_name"])
    company_line = " / ".join(part for part in [row.get("company", ""), row.get("position", "")] if part)
    if company_line:
        details.append(company_line)
    if row.get("phone"):
        details.append(row["phone"])
    return "\n".join([head] + details) if details else head


def _format_request_rows(rows, empty_text):
    if not rows:
        return empty_text
    return "\n\n".join(_format_request_row(row) for row in rows)


def _chat_error_text(lang):
    value = t(lang, "chat_error")
    return value if value != "chat_error" else "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437."


async def _chat_media_payload(update, context, text):
    message = update.message
    payload = {
        "telegram_id": update.effective_user.id,
        "full_name": update.effective_user.full_name,
        "text": text,
        "message_type": "text",
    }
    thread_id = context.user_data.get("active_admin_thread_id")
    if thread_id:
        payload["thread_id"] = thread_id
    file_obj = None
    filename = ""

    if message.location:
        payload.update({
            "message_type": "location",
            "latitude": str(message.location.latitude),
            "longitude": str(message.location.longitude),
        })
        return payload, None, ""

    telegram_file = None
    if message.photo:
        payload["message_type"] = "photo"
        photo = message.photo[-1]
        telegram_file = await photo.get_file()
        filename = f"photo_{message.message_id}.jpg"
    elif message.video:
        payload["message_type"] = "video"
        telegram_file = await message.video.get_file()
        filename = message.video.file_name or f"video_{message.message_id}.mp4"
    elif message.document:
        payload["message_type"] = "document"
        telegram_file = await message.document.get_file()
        filename = message.document.file_name or f"document_{message.message_id}"
    elif message.voice:
        payload["message_type"] = "voice"
        telegram_file = await message.voice.get_file()
        filename = f"voice_{message.message_id}.ogg"
    elif message.video_note:
        payload["message_type"] = "video_note"
        telegram_file = await message.video_note.get_file()
        filename = f"video_note_{message.message_id}.mp4"

    if telegram_file:
        buffer = BytesIO()
        await telegram_file.download_to_memory(out=buffer)
        buffer.seek(0)
        file_obj = buffer

    return payload, file_obj, filename


async def _ask_pnfl(update, lang):
    prompt = t(lang, "send_pnfl")
    if PINFL_HINT_IMAGE.exists():
        photo = BytesIO(PINFL_HINT_IMAGE.read_bytes())
        photo.name = f"pinfl_hint_{PINFL_HINT_IMAGE.stat().st_mtime_ns}.jpg"
        await update.message.reply_photo(photo=photo, caption=prompt, reply_markup=back_keyboard(lang))
    else:
        await update.message.reply_text(prompt, reply_markup=back_keyboard(lang))


async def _send_request_step(update, context, lang, state):
    context.user_data["state"] = state
    if state == states.PLATFORM:
        await update.message.reply_text(t(lang, "send_platform"), reply_markup=_choices_markup(get_platforms(), lang))
    elif state == states.PNFL:
        await _ask_pnfl(update, lang)
    elif state == states.FULL_NAME:
        await update.message.reply_text(t(lang, "send_full_name"), reply_markup=back_keyboard(lang))
    elif state == states.PASSPORT:
        await update.message.reply_text(t(lang, "send_passport"), reply_markup=back_keyboard(lang))
    elif state == states.COMPANY:
        await update.message.reply_text(t(lang, "send_station"), reply_markup=_choices_markup(get_stations(), lang))
    elif state == states.POSITION:
        await update.message.reply_text(t(lang, "send_position"), reply_markup=_choices_markup(get_positions(), lang))
    elif state == states.CAUSE:
        await update.message.reply_text(t(lang, "send_cause"), reply_markup=back_keyboard(lang))
    elif state == states.PHONE:
        await update.message.reply_text(t(lang, "send_phone"), reply_markup=contact_keyboard(lang, include_back=True))


async def _request_back(update, context, lang, state):
    previous = {
        states.PNFL: states.PLATFORM,
        states.FULL_NAME: states.PNFL,
        states.PASSPORT: states.FULL_NAME,
        states.COMPANY: states.PASSPORT,
        states.POSITION: states.COMPANY,
        states.CAUSE: states.POSITION,
        states.PHONE: states.CAUSE,
    }.get(state)
    if previous:
        await _send_request_step(update, context, lang, previous)
        return

    context.user_data.clear()
    context.user_data["lang"] = lang
    context.user_data["state"] = states.MENU
    await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu(lang))


async def _start_request(update, context, lang):
    missing = await missing_channels(context.bot, update.effective_user.id)
    if missing:
        await update.message.reply_text(t(lang, "need_subscription"), reply_markup=subscription_keyboard(missing, lang))
        return

    context.user_data.clear()
    context.user_data["lang"] = lang
    context.user_data["state"] = states.PLATFORM
    await _send_request_step(update, context, lang, states.PLATFORM)


async def _show_chat_selection(update, context, lang):
    threads = get_chat_threads(update.effective_user.id)
    buttons = []
    choices = {}
    for item in threads:
        if not item.get("id"):
            continue
        label = _thread_button_label(item)
        buttons.append({"title": label})
        choices[label] = item["id"]
    context.user_data["state"] = states.CHAT_SELECT
    context.user_data["chat_thread_choices"] = choices
    await update.message.reply_text(t(lang, "select_chat"), reply_markup=chat_select_keyboard(buttons, lang))


async def _open_admin_chat(update, context, lang, thread_id):
    context.user_data["state"] = states.CHAT
    context.user_data["active_admin_thread_id"] = thread_id
    await update.message.reply_text(t(lang, "chat_opened"), reply_markup=active_chat_keyboard(lang))


async def _new_admin_chat(update, context, lang):
    result = create_chat_thread(update.effective_user.id, update.effective_user.full_name)
    if not result.get("ok") or not result.get("id"):
        await update.message.reply_text(result.get("message") or _chat_error_text(lang), reply_markup=main_menu(lang))
        context.user_data["state"] = states.MENU
        return
    await _open_admin_chat(update, context, lang, result["id"])


async def _handle_menu_action(update, context, action, lang):
    context.user_data["lang"] = lang

    if action == "new_request":
        await _start_request(update, context, lang)
    elif action == "chat_admin":
        await _show_chat_selection(update, context, lang)
    elif action == "history":
        context.user_data["state"] = states.MENU
        data = get_intake_summary(update.effective_user.id)
        await update.message.reply_text(
            f"{t(lang, 'history_title')}\n\n{_format_request_rows(data.get('history', []), t(lang, 'no_history'))}",
            reply_markup=main_menu(lang),
        )
    elif action == "account":
        context.user_data["state"] = states.MENU
        data = get_intake_summary(update.effective_user.id)
        latest = data.get("latest")
        text = f"{t(lang, 'account_title')}\n\n{_format_request_row(latest)}" if latest else t(lang, "no_account")
        await update.message.reply_text(text, reply_markup=main_menu(lang))
    elif action == "pending":
        context.user_data["state"] = states.MENU
        data = get_intake_summary(update.effective_user.id)
        await update.message.reply_text(
            f"{t(lang, 'pending_title')}\n\n{_format_request_rows(data.get('pending', []), t(lang, 'no_pending'))}",
            reply_markup=main_menu(lang),
        )
    elif action == "settings":
        context.user_data["state"] = states.MENU
        await update.message.reply_text(t(lang, "settings_text"), reply_markup=language_keyboard())
    elif action == "developers":
        context.user_data["state"] = states.MENU
        await update.message.reply_text(t(lang, "developers_text"), reply_markup=main_menu(lang))


async def request_router(update, context):
    lang = context.user_data.get("lang", "ru")
    state = context.user_data.get("state", states.MENU)
    text = (update.message.text or update.message.caption or "").strip()
    action = _menu_action(text)

    if action:
        await _handle_menu_action(update, context, action, lang)
        return

    if _is_back(text, lang):
        if state == states.CHAT_SELECT:
            context.user_data["state"] = states.MENU
            await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu(lang))
            return
        if state == states.CHAT:
            await _show_chat_selection(update, context, lang)
            return
        if state in {states.PLATFORM, states.PNFL, states.FULL_NAME, states.PASSPORT, states.COMPANY, states.POSITION, states.CAUSE, states.PHONE}:
            await _request_back(update, context, lang, state)
            return

    if state == states.CHAT_SELECT:
        if _is_new_chat(text, lang):
            await _new_admin_chat(update, context, lang)
            return
        thread_id = context.user_data.get("chat_thread_choices", {}).get(text)
        if thread_id:
            await _open_admin_chat(update, context, lang, thread_id)
            return
        await _show_chat_selection(update, context, lang)
        return

    if state == states.CHAT:
        if _is_close_chat(text, lang):
            thread_id = context.user_data.get("active_admin_thread_id")
            if thread_id:
                close_chat_thread(update.effective_user.id, thread_id)
            context.user_data["state"] = states.MENU
            context.user_data.pop("active_admin_thread_id", None)
            await update.message.reply_text(t(lang, "chat_closed"), reply_markup=main_menu(lang))
            return
        payload, file_obj, filename = await _chat_media_payload(update, context, text)
        if payload["message_type"] == "text" and not text:
            await update.message.reply_text(t(lang, "admin_chat"), reply_markup=active_chat_keyboard(lang))
            return
        try:
            if file_obj or payload["message_type"] != "text":
                result = send_chat_media(payload, file_obj=file_obj, filename=filename)
            else:
                result = send_chat_message(payload)
        except Exception:
            result = {"ok": False}
        if result.get("ok"):
            await update.message.reply_text(t(lang, "message_sent"), reply_markup=active_chat_keyboard(lang))
        else:
            await update.message.reply_text(result.get("message") or _chat_error_text(lang), reply_markup=active_chat_keyboard(lang))
        return

    if state == states.PLATFORM:
        context.user_data["platform"] = text
        context.user_data["state"] = states.PNFL
        await _ask_pnfl(update, lang)
    elif state == states.PNFL:
        if not text.isdigit() or len(text) != 14:
            await update.message.reply_text(t(lang, "pnfl_invalid"))
            return
        context.user_data["pnfl"] = text
        context.user_data["state"] = states.FULL_NAME
        await update.message.reply_text(t(lang, "send_full_name"), reply_markup=back_keyboard(lang))
    elif state == states.FULL_NAME:
        full_name = re.sub(r"\s+", " ", text).strip()
        if len(full_name) < 5:
            await update.message.reply_text(t(lang, "full_name_invalid"), reply_markup=back_keyboard(lang))
            return
        context.user_data["full_name"] = full_name
        context.user_data["state"] = states.PASSPORT
        await update.message.reply_text(t(lang, "send_passport"), reply_markup=back_keyboard(lang))
    elif state == states.PASSPORT:
        passport = _normalize_passport(text)
        if not passport:
            await update.message.reply_text(t(lang, "passport_invalid"))
            return
        context.user_data["passport"] = passport
        context.user_data["state"] = states.COMPANY
        await update.message.reply_text(t(lang, "send_station"), reply_markup=_choices_markup(get_stations(), lang))
    elif state == states.COMPANY:
        context.user_data["company"] = text
        context.user_data["state"] = states.POSITION
        await update.message.reply_text(t(lang, "send_position"), reply_markup=_choices_markup(get_positions(), lang))
    elif state == states.POSITION:
        context.user_data["selected_position"] = text
        context.user_data["state"] = states.CAUSE
        await update.message.reply_text(t(lang, "send_cause"), reply_markup=back_keyboard(lang))
    elif state == states.CAUSE:
        context.user_data["cause"] = text
        context.user_data["state"] = states.PHONE
        await update.message.reply_text(t(lang, "send_phone"), reply_markup=contact_keyboard(lang, include_back=True))
    elif state == states.PHONE:
        raw_phone = text
        contact = update.message.contact
        if contact:
            if contact.user_id and contact.user_id != update.effective_user.id:
                await update.message.reply_text(t(lang, "phone_invalid"), reply_markup=contact_keyboard(lang, include_back=True))
                return
            raw_phone = contact.phone_number
        phone = _normalize_phone(raw_phone)
        if not phone:
            await update.message.reply_text(t(lang, "phone_invalid"), reply_markup=contact_keyboard(lang, include_back=True))
            return
        context.user_data["phone"] = phone
        payload = {
            "pnfl": context.user_data.get("pnfl"),
            "phone": context.user_data.get("phone"),
            "telegram_id": update.effective_user.id,
            "passport": context.user_data.get("passport"),
            "company": context.user_data.get("company"),
            "department": context.user_data.get("company"),
            "selected_position": context.user_data.get("selected_position"),
            "full_name": context.user_data.get("full_name", ""),
            "lang": lang,
            "cause": context.user_data.get("cause", ""),
            "platform": context.user_data.get("platform"),
            "reply_via_bot": True,
        }
        result = submit_request(payload)
        context.user_data.clear()
        context.user_data["lang"] = lang
        context.user_data["state"] = states.MENU
        message = result.get("message") or (t(lang, "sent") if result.get("ok") else t(lang, "submit_error"))
        await update.message.reply_text(message, reply_markup=main_menu(lang))
    else:
        context.user_data["state"] = states.MENU
        await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu(lang))
