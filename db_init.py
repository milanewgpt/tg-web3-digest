import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "tg_digest.sqlite3")


def main():
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
    print(f"DB initialized at: {DB_PATH}")


if __name__ == "__main__":
    main()
