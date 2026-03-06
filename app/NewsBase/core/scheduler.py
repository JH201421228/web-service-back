"""
뉴스 자동 저장 스케줄러

- APScheduler CronTrigger 사용
- 매일 오전 08:00 / 오후 19:00 에 save_news() 실행
- FastAPI lifespan 이벤트에서 start/stop
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 수집할 섹션 ID 목록 및 기사 수
_SECTION_IDS = [100, 101, 102, 103, 104, 105]   # 필요하면 추가: 101(경제), 102(사회) 등
_COUNT_PER_SECTION = 5

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def _run_save_news() -> None:
    """스케줄러 작업: 각 섹션별 뉴스 저장"""
    # 이 함수는 동기 함수이므로 직접 import 해서 실행
    from app.NewsBase.util.news_save import save_news

    for sid in _SECTION_IDS:
        try:
            logger.info("[스케줄러] 뉴스 저장 시작 (sid=%d, count=%d)", sid, _COUNT_PER_SECTION)
            save_news(section_id=sid, count=_COUNT_PER_SECTION)
            logger.info("[스케줄러] 뉴스 저장 완료 (sid=%d)", sid)
        except Exception:
            logger.exception("[스케줄러] 뉴스 저장 실패 (sid=%d)", sid)


def start_scheduler() -> None:
    """FastAPI startup 시 호출 — 스케줄러 등록 및 시작"""
    # 매일 오전 08:00
    scheduler.add_job(
        _run_save_news,
        trigger=CronTrigger(hour=7, minute=10, timezone="Asia/Seoul"),
        id="news_save_morning",
        name="뉴스 저장 (오전)",
        replace_existing=True,
        max_instances=1,          # 동일 작업 중복 실행 방지
        misfire_grace_time=600,   # 10분 내 지연 실행 허용
    )
    # 매일 오후 19:00
    scheduler.add_job(
        _run_save_news,
        trigger=CronTrigger(hour=18, minute=15, timezone="Asia/Seoul"),
        id="news_save_evening",
        name="뉴스 저장 (오후)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info("[스케줄러] 시작 — 오전 08:00 / 오후 19:00 (Asia/Seoul)")


def stop_scheduler() -> None:
    """FastAPI shutdown 시 호출"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[스케줄러] 종료")
