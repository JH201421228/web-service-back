"""
봇 스케줄러: 낮 투표, 밤 행동, 페이즈 타임아웃만 처리한다.
"""
import logging
import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

DEFAULT_VOTE_DELAY_RANGE = (0.5, 2)
DEFAULT_NIGHT_DELAY_RANGE = (0.5, 3)
FAST_NIGHT_DELAY_RANGE = (0.2, 0.8)


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.start()
    return _scheduler


def _make_job_id(game_id: str, phase: str, suffix: str = "") -> str:
    return f"reaper_{game_id}_{phase}_{suffix}"


def schedule_bot_votes(game_id: str, vote_key: str, delay_range: tuple = DEFAULT_VOTE_DELAY_RANGE, candidates=None):
    scheduler = get_scheduler()
    delay = random.uniform(*delay_range)
    run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    def _run():
        try:
            from app.Reaper.db.session import SessionLocal
            from app.Reaper.services.bot_engine import bot_submit_votes

            db = SessionLocal()
            try:
                bot_submit_votes(game_id, vote_key, db, candidates)
            finally:
                db.close()
        except Exception as e:
            logger.error("[BotScheduler] vote error for %s: %s", game_id, e)

    scheduler.add_job(_run, DateTrigger(run_date=run_at), id=_make_job_id(game_id, vote_key), replace_existing=True)


def schedule_bot_night_actions(game_id: str, delay_range: tuple = DEFAULT_NIGHT_DELAY_RANGE):
    scheduler = get_scheduler()
    delay = random.uniform(*delay_range)
    run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    def _run():
        try:
            from app.Reaper.db.session import SessionLocal
            from app.Reaper.services.bot_engine import bot_submit_night_actions

            db = SessionLocal()
            try:
                bot_submit_night_actions(game_id, db)
            finally:
                db.close()
        except Exception as e:
            logger.error("[BotScheduler] night action error for %s: %s", game_id, e)

    scheduler.add_job(_run, DateTrigger(run_date=run_at), id=_make_job_id(game_id, "night"), replace_existing=True)


def fast_track_bot_night_actions(game_id: str):
    schedule_bot_night_actions(game_id, delay_range=FAST_NIGHT_DELAY_RANGE)


def schedule_phase_timeout(game_id: str, phase: str, timeout_seconds: float):
    scheduler = get_scheduler()
    run_at = datetime.now(timezone.utc) + timedelta(seconds=timeout_seconds + 1)

    def _run():
        try:
            from app.Reaper.db.session import SessionLocal
            from app.Reaper.services.game_engine import handle_phase_timeout

            db = SessionLocal()
            try:
                handle_phase_timeout(game_id, phase, db)
            finally:
                db.close()
        except Exception as e:
            logger.error("[BotScheduler] timeout error for %s %s: %s", game_id, phase, e)

    scheduler.add_job(
        _run,
        DateTrigger(run_date=run_at),
        id=_make_job_id(game_id, phase, "timeout"),
        replace_existing=True,
    )


def start_scheduler():
    get_scheduler()
    logger.info("[BotScheduler] Reaper bot scheduler started")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    logger.info("[BotScheduler] Reaper bot scheduler stopped")
