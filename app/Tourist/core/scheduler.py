import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.Tourist.core.config import SCHEDULER_TIMEZONE
from app.Tourist.db.session import SessionLocal
from app.Tourist.models.country_snapshot import TouristCountrySnapshot
from app.Tourist.models.monthly_statistic import TouristMonthlyStatistic
from app.Tourist.models.vaccination_reference import TouristVaccinationReference
from app.Tourist.services.tourist import sync_tourist_data

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)


def _run_daily_tourist_sync() -> None:
    db = SessionLocal()
    try:
        sync_tourist_data(db)
        logger.info("[tourist-scheduler] daily sync completed")
    except Exception:
        logger.exception("[tourist-scheduler] daily sync failed")
    finally:
        db.close()


def _run_monthly_statistics_sync() -> None:
    db = SessionLocal()
    try:
        sync_tourist_data(db, include_statistics=True, force_statistics=True)
        logger.info("[tourist-scheduler] monthly statistics sync completed")
    except Exception:
        logger.exception("[tourist-scheduler] monthly statistics sync failed")
    finally:
        db.close()


def _needs_bootstrap_sync() -> bool:
    db = SessionLocal()
    try:
        return any(
            (
                db.query(TouristCountrySnapshot).count() == 0,
                db.query(TouristVaccinationReference).count() == 0,
                db.query(TouristMonthlyStatistic).count() == 0,
            )
        )
    except Exception:
        logger.warning("[tourist-scheduler] bootstrap check skipped until migrations are applied")
        return False
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.get_job("tourist_midnight_sync") is None:
        scheduler.add_job(
            _run_daily_tourist_sync,
            trigger=CronTrigger(hour=0, minute=0, timezone=SCHEDULER_TIMEZONE),
            id="tourist_midnight_sync",
            name="Tourist daily sync",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=1800,
        )

    if scheduler.get_job("tourist_monthly_statistics_sync") is None:
        scheduler.add_job(
            _run_monthly_statistics_sync,
            trigger=CronTrigger(day=1, hour=0, minute=10, timezone=SCHEDULER_TIMEZONE),
            id="tourist_monthly_statistics_sync",
            name="Tourist monthly statistics sync",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600,
        )

    if _needs_bootstrap_sync() and scheduler.get_job("tourist_bootstrap_sync") is None:
        scheduler.add_job(
            _run_monthly_statistics_sync,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=5),
            id="tourist_bootstrap_sync",
            name="Tourist bootstrap sync",
            replace_existing=True,
        )

    if not scheduler.running:
        scheduler.start()
        logger.info("[tourist-scheduler] started (daily 00:00, monthly day 1 00:10 Asia/Seoul)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[tourist-scheduler] stopped")
