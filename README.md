# TG Web3 Digest

Telegram digest pipeline for collecting Web3 messages from subscribed channels and sending scheduled summaries to a target Telegram group or chat.

The system uses a Telegram user session through Telethon, stores collected messages in SQLite, and sends digests on a configurable schedule.

## Features

- Telegram channel collection via Telethon.
- Supports explicit channel lists or all channels subscribed by the reader account.
- SQLite storage.
- Scheduled digests by local timezone.
- Railway entrypoint and systemd units.
- Separate collector and sender sessions to reduce lock contention.

## Environment

```bash
cp .env.example .env
```

Required variables:

- `TG_API_ID` — Telegram API ID from `my.telegram.org`.
- `TG_API_HASH` — Telegram API hash from `my.telegram.org`.
- `TG_SESSION_STRING` — Telethon StringSession.
- `TG_CHANNELS` — comma-separated channels or `ALL`.
- `TG_TARGET` — destination chat/group name or username.
- `DB_PATH` — SQLite database path.
- `POLL_SECONDS` — collector poll interval.
- `SEND_HOURS` — comma-separated local hours.
- `TZ_DIGEST` — digest timezone.
- `MAX_ITEMS` — max items per digest.
- `MAX_CHARS_PER_ITEM` — max characters per item.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python3 db_init.py
```

## First Telethon Login

Run the sender once to generate or validate the Telethon session:

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python3 tg_digest_sender.py
```

On first run, Telethon asks for the reader account phone and login code. Keep the generated session safe.

## Manual Test

```bash
python3 tg_digest_collector.py
python3 tg_digest_sender.py
```

Confirm the digest appears in the configured target chat.

## Deployment

Available deployment options:

- Railway through `main.py` and `railway.toml`.
- systemd through files in `systemd/`.

For full VPS/systemd details, see [`README_SETUP.md`](./README_SETUP.md).

## Security

- Do not commit `.env` or Telethon session files.
- Treat `TG_SESSION_STRING` like a password.
- Use a dedicated reader account where possible.
