"""
Combined entry point for Railway:
- Collector: every hour at :30
- Sender: 08:00, 11:00, 14:00, 17:00 Asia/Jerusalem
- Exporter: daily at 01:00 UTC — SQLite → /data/sources/*.md
- API server: HTTP on $PORT — serves /data/sources/ for tg-notebooklm
"""
import asyncio
import logging
import os
import threading

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SEND_HOURS = [int(h) for h in os.environ.get("SEND_HOURS", "8,11,14,17").split(",")]
TZ = pytz.timezone(os.environ.get("TZ_DIGEST", "Asia/Jerusalem"))


async def run_collector():
    from tg_digest_collector import run
    await run()


async def run_sender():
    from tg_digest_sender import run
    await run()


async def collector_job():
    try:
        log.info("Collector: starting poll")
        await run_collector()
        log.info("Collector: poll done")
    except Exception as e:
        log.error("Collector error: %r", e)


async def sender_job():
    try:
        log.info("Sender: starting digest")
        await run_sender()
        log.info("Sender: done")
    except Exception as e:
        log.error("Sender error: %r", e)


async def exporter_job():
    try:
        log.info("Exporter: starting")
        from tg_digest_exporter import run
        run()
        log.info("Exporter: done")
    except Exception as e:
        log.error("Exporter error: %r", e)


async def main():
    # HTTP API server in background thread (serves /data/sources/ for tg-notebooklm)
    from tg_digest_api import start_server, register_send_callback
    register_send_callback(asyncio.get_event_loop(), sender_job)
    threading.Thread(target=start_server, daemon=True).start()

    scheduler = AsyncIOScheduler(timezone=TZ)

    scheduler.add_job(collector_job, "cron", minute=30, misfire_grace_time=600)
    log.info("Collector scheduled every hour at :30")

    for hour in SEND_HOURS:
        scheduler.add_job(sender_job, "cron", hour=hour, minute=0, misfire_grace_time=600)
        log.info("Sender scheduled at %02d:00 %s", hour, TZ.zone)

    scheduler.add_job(exporter_job, "cron", hour=1, minute=0,
                      timezone=pytz.utc, misfire_grace_time=1800)
    log.info("Exporter scheduled daily at 01:00 UTC")

    scheduler.start()

    asyncio.create_task(collector_job())
    asyncio.create_task(exporter_job())  # export on startup too

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
