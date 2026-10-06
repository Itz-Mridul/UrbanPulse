"""
Background data ingestion scheduler.
Polls for new sensor data and triggers inference on significant changes.
"""
import asyncio
from loguru import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

_scheduler = None


async def ingest_and_check():
    """Periodic task: check for new data, run inference if threshold crossed."""
    logger.debug("Ingestion check tick — no live feed in MVP mode.")
    # In MVP: data is static/historical. Live feed simulation happens via replay API.
    # Future: pull from IMD/CWC APIs and trigger predictions.router.trigger_inference()


async def start_scheduler():
    global _scheduler
    if not SCHEDULER_AVAILABLE:
        logger.warning("APScheduler not installed — background ingestion disabled.")
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(ingest_and_check, "interval", minutes=5, id="ingestion")
    _scheduler.start()
    logger.info("Background ingestion scheduler started (5-min interval).")


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
