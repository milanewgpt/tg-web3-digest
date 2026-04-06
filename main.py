"""
Combined entry point for Railway:
- Collector runs every POLL_SECONDS in a background asyncio task
- Sender is scheduled at 08:00, 11:00, 14:00, 19:00 Asia/Jerusalem via APScheduler
"""
import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "3600"))
SEND_HOURS = [int(h) for h in os.environ.get("SEND_HOURS", "8,11,14,19").split(",")]
TZ = pytz.timezone(os.environ.get("TZ_DIGEST", "Asia/Jerusalem"))


async def run_collector():
    """Wrapper: import lazily so env vars are set before module-level code runs."""
    from tg_digest_collector import run
    await run()


async def run_sender():
    from tg_digest_sender import run
    await run()


async def collector_loop():
    while True:
        try:
            log.info("Collector: starting poll")
            await run_collector()
            log.info("Collector: poll done, sleeping %ss", POLL_SECONDS)
        except Exception as e:
            log.error("Collector error: %r", e)
        await asyncio.sleep(POLL_SECONDS)


async def sender_job():
    try:
        log.info("Sender: starting digest")
        await run_sender()
        log.info("Sender: done")
    except Exception as e:
        log.error("Sender error: %r", e)


async def main():
    scheduler = AsyncIOScheduler(timezone=TZ)
    for hour in SEND_HOURS:
        scheduler.add_job(sender_job, "cron", hour=hour, minute=0, misfire_grace_time=600)
        log.info("Sender scheduled at %02d:00 %s", hour, TZ.zone)
    scheduler.start()

    await collector_loop()


if __name__ == "__main__":
    asyncio.run(main())
