import os
import datetime
import asyncio
import feedparser
import openai
from telegram import Bot
from io import BytesIO
import requests

# ======== CONFIG ========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ленты: топ крипто+финансы (можно добавить свои)
RSS_FEEDS = [
    # Крипто
    "https://cointelegraph.com/rss",      # Cointelegraph
    "https://www.coindesk.com/arc/outboundfeeds/rss/",  # Coindesk
    "https://decrypt.co/feed",            # Decrypt
    # Финансы
    "https://www.bloomberg.com/feed/podcast/etf-report.xml",  # Bloomberg (пример)
    "https://www.investing.com/rss/news_301.rss",     # Investing.com
    # Дополняй по желанию!
]

NEWS_COUNT = 7    # Cколько новостей брать (5-7)
LANGS = ['ru', 'en']  # Для перевода
SIGNATURE = "Best regards, @ReserveOne"

# ======== UTILS ========

def get_feed_news(feeds, max_news):
    # Собираем уникальные новости с разных лент (по времени)
    entries = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
            entries.extend(d.entries)
        except Exception as e:
            print(f"Error parsing {url}: {e}")
    # Сортируем по дате, берём свежие, убираем дубли по ссылке
    entries = sorted(entries, key=lambda e: e.get("published_parsed", datetime.datetime.now().timetuple()), reverse=True)
    seen = set()
    fresh_news = []
    for e in entries:
        link = e.get("link")
        if link and link not in seen:
            seen.add(link)
            title = e.get("title", "")
            summary = e.get("summary", "")
            fresh_news.append({"title": title, "summary": summary, "link": link})
        if len(fresh_news) >= max_news:
            break
    return fresh_news

def split_summary(text):
    # Оставить только 1–2 предложения (сжато)
    if not text:
        return ""
    sentences = text.replace('\n', ' ').split('. ')
    return '. '.join(sentences[:2]).strip() + ('.' if sentences else '')

def ai_translate(text, lang, key):
    # Перевод через OpenAI (дешево, быстро, нейросеть)
    if lang == 'en':
        return text  # Оригинал на английском
    client = openai.OpenAI(api_key=key)
    prompt = f"Переведи кратко и с легкой шуткой на русский:\n{text}"
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a witty, professional news translator."},
                      {"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.8
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("Translation error:", e)
        return text

def ai_english_joke(text, key):
    # Для английского можно добавить легкий шуточный оборот (если хочешь)
    client = openai.OpenAI(api_key=key)
    prompt = f"Rephrase this crypto/finance news for Telegram, keep it short, smart, and add a light business-style joke or witty note at the end:\n{text}"
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a professional financial Telegram copywriter."},
                      {"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.8
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("EN-joke error:", e)
        return text

def ai_generate_image(main_news, key):
    # Генерируем DALL-E картинку с юмором, но профессионально
    prompt = f"""Digital illustration for a Telegram crypto/finance digest, inspired by this news: "{main_news}". 
    Style: fun, witty, but professional, modern office cartoon, soft colors, no text, no faces, news illustration."""
    client = openai.OpenAI(api_key=key)
    try:
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        img_url = resp.data[0].url
        img_data = requests.get(img_url).content
        return BytesIO(img_data)
    except Exception as e:
        print("DALL-E error:", e)
        return None

# ======== DIGEST GENERATION ========

async def send_digest():
    print("Collecting news...")
    news_list = get_feed_news(RSS_FEEDS, NEWS_COUNT)
    print(f"Found {len(news_list)} news")

    post_blocks = []
    for i, news in enumerate(news_list):
        en_text = news["title"]
        ru_text = ai_translate(en_text, 'ru', OPENAI_API_KEY)
        en_joke = ai_english_joke(en_text, OPENAI_API_KEY)
        link = news["link"]
        block = f"🦾 {ru_text}\n{en_joke}\n[Подробнее / Read more]({link})\n"
        post_blocks.append(block)
        print(f"Block {i+1} done")

    post_text = "\n".join(post_blocks) + f"\n\n{SIGNATURE}"
    # Проверка лимита Telegram (4096 символов на сообщение)
    if len(post_text) > 4000:
        post_text = "\n".join(post_blocks[:5]) + f"\n\n{SIGNATURE}"

    print("Generating image for main news...")
    img_data = ai_generate_image(news_list[0]['title'], OPENAI_API_KEY)
    bot = Bot(token=TELEGRAM_TOKEN)

    if img_data:
        await bot.send_photo(
            chat_id=TELEGRAM_CHANNEL,
            photo=img_data,
            caption="Crypto & Finance Digest 📰",  # короткий caption для фото
        )
        await asyncio.sleep(2)  # Для надёжности, чтобы фото успело загрузиться

    print("Sending news digest...")
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL,
        text=post_text,
        parse_mode="Markdown"
    )
    print("Digest sent!")

# ======== RUN MAIN ========

if __name__ == "__main__":
    print("Crypto/Finance News Digest is running...")
    asyncio.run(send_digest())
