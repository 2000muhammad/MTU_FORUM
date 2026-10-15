from io import BytesIO
from pathlib import Path

from app.keyboards import language_keyboard


LANGUAGE_PICKER_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "language_selected.png"


async def send_language_picker(message, prompt):
    if LANGUAGE_PICKER_IMAGE.exists():
        photo = BytesIO(LANGUAGE_PICKER_IMAGE.read_bytes())
        photo.name = f"language_picker_{LANGUAGE_PICKER_IMAGE.stat().st_mtime_ns}.png"
        await message.reply_photo(photo=photo, caption=prompt, reply_markup=language_keyboard())
    else:
        await message.reply_text(prompt, reply_markup=language_keyboard())
