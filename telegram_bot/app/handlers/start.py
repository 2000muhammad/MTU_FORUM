from app.keyboards import contact_keyboard
from app.language_picker import send_language_picker
from app.texts import t
from app.api import complete_password_reset


async def start(update, context):
    if update.effective_user is None or context.user_data is None or update.message is None:
        return
    context.user_data.clear()
    argument = context.args[0] if context.args else ""
    if argument.startswith("reset_"):
        result = complete_password_reset(argument.removeprefix("reset_"), update.effective_user.id)
        if result.get("ok"):
            await update.message.reply_text(
                "Пароль восстановлен.\n"
                f"Логин: {result['username']}\n"
                f"Новый пароль: {result['password']}\n\n"
                "После входа смените пароль в профиле."
            )
        else:
            await update.message.reply_text(
                result.get("message") or "Ссылка недействительна или истекла. Запросите новую ссылку на странице входа."
            )
        return
    if argument.startswith("bind_"):
        context.user_data["telegram_bind_token"] = argument.removeprefix("bind_")
        context.user_data["state"] = "telegram_bind_contact"
        await update.message.reply_text(
            "Для привязки профиля отправьте свой номер кнопкой ниже. Номер должен совпадать с номером в профиле MTU FORUM.",
            reply_markup=contact_keyboard("ru"),
        )
        return
    await send_language_picker(update.message, t("ru", "choose_language"))
