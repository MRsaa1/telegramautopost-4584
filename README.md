[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#) [![License](https://img.shields.io/badge/License-Proprietary-lightgrey)](#) [![Status](https://img.shields.io/badge/Build-OK-success)](#)

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

## Usage

### Environment (.env)
Create `.env` with your keys:
```
TELEGRAM_BOT_TOKEN=xxxxx
OPENAI_API_KEY=xxxxx
OTHER_SECRET=xxxxx
```

### Run locally
```
python main.py
```

### Run on schedule (cron)
```
*/30 * * * *  cd $(pwd) && /usr/bin/python3 main.py >> run.log 2>&1
```

## Examples
- Startup without sending: dry-run flag (if supported)
- Custom channel/topic configuration via env
- Replit: add secrets in the Secrets panel and click Run
