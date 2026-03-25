"""
뉴스 자동 저장 스케줄러

- APScheduler CronTrigger 사용
- 매일 오전 08:00 / 오후 19:00 에 save_news() 실행
- Google News 검색 ("주식", "비트코인") 스케줄도 함께 실행
- FastAPI lifespan 이벤트에서 start/stop
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 수집할 섹션 ID 목록 및 기사 수
_SECTION_IDS = [100, 101, 102, 103, 104, 105]   # 필요하면 추가: 101(경제), 102(사회) 등
_COUNT_PER_SECTION = 5

# Google News 검색 키워드 → section_id 매핑
_GOOGLE_NEWS_KEYWORDS = {
    "주식": 200,
    "비트코인": 201,
}
_GOOGLE_NEWS_COUNT = 5

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def _run_save_news() -> None:
    """스케줄러 작업: 각 섹션별 네이버 뉴스 저장"""
    from app.NewsBase.util.news_save import save_news

    for sid in _SECTION_IDS:
        try:
            logger.info("[스케줄러] 뉴스 저장 시작 (sid=%d, count=%d)", sid, _COUNT_PER_SECTION)
            save_news(section_id=sid, count=_COUNT_PER_SECTION)
            logger.info("[스케줄러] 뉴스 저장 완료 (sid=%d)", sid)
        except Exception:
            logger.exception("[스케줄러] 뉴스 저장 실패 (sid=%d)", sid)


def _run_save_google_news() -> None:
    """스케줄러 작업: Google News 검색 키워드별 뉴스 저장"""
    from app.NewsBase.util.google_news_save import save_google_news

    for keyword, section_id in _GOOGLE_NEWS_KEYWORDS.items():
        try:
            logger.info(
                "[스케줄러] Google News 저장 시작 (keyword='%s', sid=%d, count=%d)",
                keyword, section_id, _GOOGLE_NEWS_COUNT,
            )
            save_google_news(
                keyword=keyword,
                section_id=section_id,
                count=_GOOGLE_NEWS_COUNT,
            )
            logger.info(
                "[스케줄러] Google News 저장 완료 (keyword='%s', sid=%d)",
                keyword, section_id,
            )
        except Exception:
            logger.exception(
                "[스케줄러] Google News 저장 실패 (keyword='%s', sid=%d)",
                keyword, section_id,
            )


def start_scheduler() -> None:
    """FastAPI startup 시 호출 — 스케줄러 등록 및 시작"""
    # ── 네이버 뉴스 ──
    # 매일 오전 07:10
    scheduler.add_job(
        _run_save_news,
        trigger=CronTrigger(hour=7, minute=00, timezone="Asia/Seoul"),
        id="news_save_morning",
        name="뉴스 저장 (오전)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )
    # 매일 오후 17:10
    scheduler.add_job(
        _run_save_news,
        trigger=CronTrigger(hour=17, minute=00, timezone="Asia/Seoul"),
        id="news_save_evening",
        name="뉴스 저장 (오후)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )

    # ── Google News 검색 (주식 / 비트코인) ──
    # 네이버 뉴스 작업과 15분 간격으로 실행 (API 부하 분산)
    # 매일 오전 07:25
    scheduler.add_job(
        _run_save_google_news,
        trigger=CronTrigger(hour=7, minute=20, timezone="Asia/Seoul"),
        id="google_news_save_morning",
        name="Google News 저장 (오전)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )
    # 매일 오후 17:25
    scheduler.add_job(
        _run_save_google_news,
        trigger=CronTrigger(hour=17, minute=20, timezone="Asia/Seoul"),
        id="google_news_save_evening",
        name="Google News 저장 (오후)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info(
        "[스케줄러] 시작 — 네이버: 07:00/17:00, Google News: 07:20/17:20 (Asia/Seoul)"
    )


def stop_scheduler() -> None:
    """FastAPI shutdown 시 호출"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[스케줄러] 종료")
