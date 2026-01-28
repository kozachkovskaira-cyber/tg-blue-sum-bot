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

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        lower_blue = np.array([85, 30, 30])
        upper_blue = np.array([145, 255, 255])

        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        result = cv2.bitwise_and(img, img, mask=mask)

        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        text = pytesseract.image_to_string(gray, config='--psm 6')
        numbers = list(map(int, re.findall(r'\d+', text)))

        if not numbers:
            await message.reply(
                "🤔 Я не знайшла сині цифри.\n"
                "Спробуй інший скрін або кращу якість."
            )
            return

        await message.reply(
            f"🔢 Знайдено: {numbers}\n"
            f"✅ СУМА: {sum(numbers)}"
        )

    except Exception as e:
        await message.reply(f"⚠️ Помилка обробки фото:\n{e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
