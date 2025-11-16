# telegramautopost-4584

Telegram autopost bot: news/digest publishing with caching and retries.

## Features
- Scheduled/cron-friendly execution
- Robust logging (local only, logs ignored by Git)
- Secrets via `.env`/JSON (never committed)
- Replit/Local friendly (uv/pip)

## Quick start

```bash
# 1) Create and activate venv (optional)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt || true
if command -v uv >/dev/null 2>&1; then
  uv pip install -r requirements.txt || true
fi

# 3) Create .env (DO NOT COMMIT!)
cp .env.example .env 2>/dev/null || true
# Then edit .env with your real values

# 4) Run
python main.py
```

## Environment variables (store in .env)
- TELEGRAM_BOT_TOKEN=
- OPENAI_API_KEY=
- OTHER_SECRET=

Never commit `.env`, `*.json` credentials or logs. They are ignored via `.gitignore`.

## Deployment
- Replit: add keys in Secrets, run `main.py`
- Cron: schedule `python main.py`

## License
Proprietary. All rights reserved.
