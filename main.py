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

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("👋 Бот онлайн. Надішли скрін 📸")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, "image.jpg")

    img = cv2.imread("image.jpg")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([90, 60, 60])
    upper_blue = np.array([140, 255, 255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(img, img, mask=mask)

    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    text = pytesseract.image_to_string(gray, config='--psm 6 digits')
    numbers = list(map(int, re.findall(r'\d+', text)))

    if numbers:
        await message.reply(
            "🔢 Знайдено:\n" +
            " + ".join(map(str, numbers)) +
            f"\n\n✅ СУМА: {sum(numbers)}"
        )
    else:
        await message.reply("❌ Сині цифри не знайдені")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
