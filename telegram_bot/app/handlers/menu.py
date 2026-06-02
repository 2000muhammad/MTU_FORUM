from app import states
from app.keyboards import language_keyboard, main_menu, subscription_keyboard
from app.subscription import missing_channels
from app.texts import t


async def send_menu_after_subscription(message, context, user_id, lang):
    missing = await missing_channels(context.bot, user_id)
    if missing:
        await message.reply_text(t(lang, "need_subscription"), reply_markup=subscription_keyboard(missing, lang))
        return False

    context.user_data["state"] = states.MENU
    await message.reply_text(t(lang, "welcome"), reply_markup=main_menu(lang))
    return True


async def menu_router(update, context):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "ru")

    if query.data.startswith("lang:"):
        lang = query.data.split(":", 1)[1]
        context.user_data.clear()
        context.user_data["lang"] = lang
        await query.edit_message_text(t(lang, "language_saved"))
        await send_menu_after_subscription(query.message, context, query.from_user.id, lang)
        return

    if query.data == "check_subscription":
        missing = await missing_channels(context.bot, query.from_user.id)
        if missing:
            await query.edit_message_text(t(lang, "need_subscription"), reply_markup=subscription_keyboard(missing, lang))
            return

        await query.edit_message_text(t(lang, "subscription_ok"))
        await query.message.reply_text(t(lang, "welcome"), reply_markup=main_menu(lang))
        context.user_data["state"] = states.MENU
        return

    if query.data == "settings":
        await query.message.reply_text(t(lang, "settings_text"), reply_markup=language_keyboard())
