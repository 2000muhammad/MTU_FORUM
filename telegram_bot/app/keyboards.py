from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from app.texts import t


LANGUAGE_CODES = ("ru", "uz", "uz-cyrl", "en")


def language_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("RU", callback_data="lang:ru"),
        InlineKeyboardButton("UZ", callback_data="lang:uz"),
        InlineKeyboardButton("УЗ", callback_data="lang:uz-cyrl"),
        InlineKeyboardButton("EN", callback_data="lang:en"),
    ]])


def menu_labels(lang="ru"):
    return {
        "new_request": t(lang, "menu_new_request"),
        "account": t(lang, "menu_account"),
        "history": t(lang, "menu_history"),
        "pending": t(lang, "menu_pending"),
        "chat_admin": t(lang, "menu_chat_admin"),
        "settings": t(lang, "menu_settings"),
        "developers": t(lang, "menu_developers"),
    }


def all_menu_labels():
    labels = {}
    for lang in LANGUAGE_CODES:
        for action, label in menu_labels(lang).items():
            labels[label] = action
    return labels


def main_menu(lang="ru"):
    labels = menu_labels(lang)
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(labels["new_request"]), KeyboardButton(labels["account"])],
            [KeyboardButton(labels["history"]), KeyboardButton(labels["pending"])],
            [KeyboardButton(labels["chat_admin"]), KeyboardButton(labels["settings"])],
            [KeyboardButton(labels["developers"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def subscription_keyboard(channels, lang="ru"):
    rows = [[InlineKeyboardButton(ch["name"], url=ch["url"])] for ch in channels]
    rows.append([InlineKeyboardButton(t(lang, "check_subscription"), callback_data="check_subscription")])
    return InlineKeyboardMarkup(rows)


def back_label(lang="ru"):
    return t(lang, "back")


def close_chat_label(lang="ru"):
    return t(lang, "close_chat")


def new_chat_label(lang="ru"):
    return t(lang, "new_chat")


def choice_keyboard(items, lang="ru", include_back=False):
    rows = [[item["name"]] for item in items]
    if include_back:
        rows.append([back_label(lang)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


def contact_keyboard(lang="ru", include_back=False):
    rows = [[KeyboardButton(t(lang, "share_contact"), request_contact=True)]]
    if include_back:
        rows.append([back_label(lang)])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def back_keyboard(lang="ru"):
    return ReplyKeyboardMarkup([[back_label(lang)]], resize_keyboard=True, one_time_keyboard=True)


def chat_select_keyboard(threads, lang="ru"):
    rows = [[new_chat_label(lang)]]
    rows.extend([[item["title"]] for item in threads])
    rows.append([back_label(lang)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


def active_chat_keyboard(lang="ru"):
    return ReplyKeyboardMarkup([[back_label(lang), close_chat_label(lang)]], resize_keyboard=True, is_persistent=True)
