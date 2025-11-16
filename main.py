#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
import openai
import gspread
from google.oauth2.service_account import Credentials
from telegram import Bot
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from io import BytesIO
import aiohttp

# >>> Добавлено для изменения размера
from PIL import Image

# --- ЛОГИ ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('autopost_9.log', maxBytes=1e6, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- НАСТРОЙКИ ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
JSON_KEY_FILE = os.getenv("JSON_KEY_FILE")

# Канал (EN отключён)
TELEGRAM_CHANNEL_RU = "-1002597393191"

# >>> Целевая высота, ширина сохраняется (можно задать в Secrets)
TARGET_IMAGE_HEIGHT = int(os.getenv("TARGET_IMAGE_HEIGHT", "750"))

# --- ЗАГРУЗКА ТЕМЫ ---
def get_today_topic():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(JSON_KEY_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        sheet = gc.open(SPREADSHEET_NAME).sheet1
        day_name = datetime.now().strftime("%A")
        records = sheet.get_all_records()
        today = next(
            (row for row in records if row["Day"].strip().lower() == day_name.strip().lower()),
            None
        )
        if today:
            return today["Topic"]
        else:
            raise ValueError(f"No topic found for {day_name}")
    except Exception as e:
        logger.error(f"Error reading topic: {e}")
        raise

# --- AI (RUSSIAN minimal humor, friendly) ---
async def ai_generate_text_ru(topic):
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            f"Напиши структурированный пост в Telegram на русском языке (до 800 символов) по теме: '{topic}'. "
            "Стиль: дружелюбный, лёгкий, информативный, с минимальным юмором (без иронии). "
            "Формат: жирный заголовок, 2–3 предложения объяснения, 1–2 пункта со смайликами ✅ или 🔥."
        )
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — финансовый обозреватель, пишущий простым и дружелюбным языком."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI RU text error: {e}")
        raise

# >>> Небольшой хелпер для изменения высоты
def _resize_image_height(buf: BytesIO, target_height: int) -> BytesIO:
    """
    Уменьшает высоту изображения до target_height, ширину оставляет как есть.
    Если картинка уже не выше — возвращает исходную.
    """
    try:
        img = Image.open(buf)
        w, h = img.size
        if h <= target_height:
            buf.seek(0)
            return buf
        resized = img.resize((w, target_height), Image.Resampling.LANCZOS)
        out = BytesIO()
        resized.save(out, format="PNG")
        out.seek(0)
        return out
    except Exception as e:
        logger.error(f"Resize error: {e}")
        buf.seek(0)
        return buf

# --- AI IMAGE ---
async def ai_generate_image(prompt):
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        img_prompt = (
            f"Digital illustration for a finance topic: '{prompt}'. "
            "Fun but professional, modern flat style, soft colors, no text."
        )
        resp = await client.images.generate(
            model="dall-e-3",
            prompt=img_prompt,
            n=1,
            size="1024x1024"
        )
        img_url = resp.data[0].url
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp_img:
                buf = BytesIO(await resp_img.read())

        # >>> Единственное изменение: уменьшаем высоту (ширина 그대로)
        buf = _resize_image_height(buf, TARGET_IMAGE_HEIGHT)
        return buf
    except Exception as e:
        logger.error(f"AI image error: {e}")
        raise

# --- TELEGRAM SEND ---
async def send_to_telegram(chat_id, text, image):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_photo(
            chat_id=chat_id,
            photo=image,
            caption=text[:1024],
            parse_mode="HTML"
        )
        logger.info(f"Post sent successfully to {chat_id}")
    except Exception as e:
        logger.error(f"Telegram error for {chat_id}: {e}")
        raise

# --- MAIN ---
async def main():
    logger.info("🚀 Running 9:00 autopost (Topic of the Day)")
    topic = get_today_topic()
    logger.info(f"Topic: {topic}")

    # Генерация текста (только RU)
    post_text_ru = await ai_generate_text_ru(topic)

    # Хвост поста
    tail = "\n\nС уважением, ReserveOne"

    # Итоговый пост
    full_text_ru = f"💡 <b>Тема дня:</b> {topic}\n\n{post_text_ru}{tail}"

    # Генерация картинки (с автосжатием по высоте)
    image = await ai_generate_image(topic)

    # Отправка в русскоязычный канал
    await send_to_telegram(TELEGRAM_CHANNEL_RU, full_text_ru, image)

if __name__ == "__main__":
    asyncio.run(main())
