"""
Combined entry point for Railway:
- Collector runs every hour at :30 (1:30, 2:30, ...) via APScheduler
- Sender runs at 08:00, 11:00, 14:00, 17:00 Asia/Jerusalem via APScheduler
Collector and sender are offset by 30 min so they never overlap.
"""
import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SEND_HOURS = [int(h) for h in os.environ.get("SEND_HOURS", "8,11,14,17").split(",")]
TZ = pytz.timezone(os.environ.get("TZ_DIGEST", "Asia/Jerusalem"))


async def run_collector():
    """Wrapper: import lazily so env vars are set before module-level code runs."""
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


async def main():
    scheduler = AsyncIOScheduler(timezone=TZ)

    # Collector: every hour at :30
    scheduler.add_job(collector_job, "cron", minute=30, misfire_grace_time=600)
    log.info("Collector scheduled every hour at :30")

    # Sender: at fixed hours at :00
    for hour in SEND_HOURS:
        scheduler.add_job(sender_job, "cron", hour=hour, minute=0, misfire_grace_time=600)
        log.info("Sender scheduled at %02d:00 %s", hour, TZ.zone)

    scheduler.start()

    # Run collector immediately on startup (as a task, non-blocking)
    asyncio.create_task(collector_job())

    # Keep process alive
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
