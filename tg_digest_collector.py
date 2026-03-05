import os
import sqlite3
import time
from datetime import timezone

from telethon import TelegramClient
from telethon.errors import FloodWaitError

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ.get("TG_SESSION", "reader_session")

CHANNELS = [c.strip() for c in os.environ["TG_CHANNELS"].split(",") if c.strip()]
DB_PATH = os.environ.get("DB_PATH", "tg_digest.sqlite3")
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "900"))  # 15 minutes default (quiet)


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL,
        msg_id INTEGER NOT NULL,
        date_utc TEXT NOT NULL,
        text TEXT NOT NULL,
        UNIQUE(channel, msg_id)
    )
    """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """
    )
    con.commit()
    con.close()


def get_last_id(con, channel):
    cur = con.cursor()
    cur.execute("SELECT value FROM state WHERE key = ?", (f"last_id:{channel}",))
    row = cur.fetchone()
    return int(row[0]) if row else 0


def set_last_id(con, channel, last_id):
    cur = con.cursor()
    cur.execute(
        "INSERT INTO state(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (f"last_id:{channel}", str(last_id)),
    )
    con.commit()


def save_message(con, channel, msg_id, dt, text):
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO messages(channel, msg_id, date_utc, text) VALUES (?, ?, ?, ?)",
        (channel, msg_id, dt, text),
    )


def utc_iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


async def run():
    init_db()
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()  # first run will ask for code in console

    while True:
        try:
            con = sqlite3.connect(DB_PATH)
            for ch in CHANNELS:
                last_id = get_last_id(con, ch)
                entity = await client.get_entity(ch)

                new_last = last_id
                # reverse=True yields ascending order; min_id ensures only new messages
                async for msg in client.iter_messages(entity, min_id=last_id, reverse=True):
                    if not msg.message:
                        continue
                    text = msg.message.strip()
                    if not text:
                        continue
                    save_message(con, ch, msg.id, utc_iso(msg.date), text)
                    if msg.id > new_last:
                        new_last = msg.id

                if new_last != last_id:
                    set_last_id(con, ch, new_last)

            con.commit()
            con.close()

        except FloodWaitError as e:
            time.sleep(int(e.seconds) + 5)
        except Exception as e:
            print("Collector error:", repr(e))
            time.sleep(30)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
