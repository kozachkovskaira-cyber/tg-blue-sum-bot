import logging
import os
import cv2
import pytesseract
import numpy as np
import re
from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(level=logging.INFO)

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(content_types=['photo', 'document'])
async def handle_photo(message: types.Message):
    try:
        await message.reply("📸 Фото отримала, аналізую...")

        # --- отримуємо file_id ---
        if message.photo:
            file_id = message.photo[-1].file_id
        elif (
            message.document
            and message.document.mime_type
            and message.document.mime_type.startswith("image")
        ):
            file_id = message.document.file_id
        else:
            await message.reply("❌ Це не зображення")
            return

        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, "image.jpg")

        img = cv2.imread("image.jpg")
        if img is None:
            await message.reply("❌ Не вдалося зчитати зображення")
            return

        # --- беремо ТІЛЬКИ праву колонку ---
        h, w, _ = img.shape
        crop = img[:, int(w * 0.65):w]

        # --- підготовка для OCR ---
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        gray = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        # --- OCR: читаємо окремі рядки ---
        data = pytesseract.image_to_data(
    gray,
    output_type=pytesseract.Output.DICT,
    config='--psm 11 -c tessedit_char_whitelist=0123456789'
)

numbers = []

img_width = gray.shape[1]

for i in range(len(data["text"])):
    txt = data["text"][i].strip()
    if not txt.isdigit():
        continue

    value = int(txt)

    # subscriber count: 0–999
    if not (0 <= value <= 999):
        continue

    x = data["left"][i]
    w = data["width"][i]

    # 🎯 беремо ТІЛЬКИ те, що майже максимально праворуч
    if x + w >= img_width * 0.9:
        numbers.append(value)

        # --- якщо нічого не знайшли ---
        if not numbers:
            await message.reply(
                "🤔 Я не знайшла сині цифри.\n"
                "Спробуй інший скрін або кращу якість."
            )
            return

        # --- фінальна відповідь ---
        await message.reply(
            f"🔢 Знайдено: {numbers}\n"
            f"✅ СУМА: {sum(numbers)}"
        )

    except Exception as e:
        await message.reply("⚠️ Помилка під час обробки фото.")
        print(e)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
