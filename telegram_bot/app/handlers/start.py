from app.keyboards import language_keyboard
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
    await update.message.reply_text(t("ru", "choose_language"), reply_markup=language_keyboard())
