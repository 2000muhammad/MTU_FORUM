import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.config import BOT_TOKEN
from app.handlers.start import start
from app.handlers.menu import menu_router
from app.handlers.request_flow import request_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_router, pattern="^(lang:|check_subscription|settings)"))
    app.add_handler(MessageHandler(
        (filters.TEXT & ~filters.COMMAND)
        | filters.CONTACT
        | filters.PHOTO
        | filters.VIDEO
        | filters.Document.ALL
        | filters.VOICE
        | filters.VIDEO_NOTE
        | filters.LOCATION,
        request_router,
    ))
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
