from app.keyboards import language_keyboard
from app.texts import t


async def start(update, context):
    context.user_data.clear()
    await update.message.reply_text(t("ru", "choose_language"), reply_markup=language_keyboard())
