"""
Google News 검색 뉴스 수집 → 요약/퀴즈 생성 → DB 저장

- Google News에서 특정 키워드로 검색한 상위 뉴스를 수집
- 기존 news_summary 모듈을 활용해 요약+퀴즈 생성
- 기존 News 모델에 저장 (section_id: 200=주식, 201=비트코인)
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# BE 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.NewsBase.core.config import build_db_url                           # noqa: E402
from app.NewsBase.models.news import News                                   # noqa: E402
from app.NewsBase.util.google_news_search import fetch_google_news_urls     # noqa: E402
from app.NewsBase.util.news_summary import fetch_news_content, summarize_and_quiz  # noqa: E402

from sqlalchemy import create_engine         # noqa: E402
from sqlalchemy.orm import sessionmaker      # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB 세션 (이 스크립트 전용)
# ---------------------------------------------------------------------------

_engine = create_engine(build_db_url(), pool_pre_ping=True)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# ---------------------------------------------------------------------------
# 저장 함수
# ---------------------------------------------------------------------------

KST = timezone(timedelta(hours=9))


def _when_flag() -> int:
    """현재 시각 기준 오전(0) / 오후(1) 반환 (KST 기준)"""
    return 0 if datetime.now(tz=KST).hour < 12 else 1


def save_google_news(keyword: str, section_id: int, count: int = 5) -> None:
    """
    Google News에서 keyword로 검색한 상위 기사를 수집·요약·저장합니다.

    Args:
        keyword    : 검색 키워드 (예: "주식", "비트코인")
        section_id : DB에 저장할 섹션 ID (200=주식, 201=비트코인)
        count      : 저장할 기사 수 (기본 5)
    """
    logger.info(
        "Google News 수집 시작 (keyword='%s', section_id=%d, count=%d)",
        keyword, section_id, count,
    )

    # 1. Google News RSS에서 URL 수집
    news_items = fetch_google_news_urls(keyword=keyword, count=count)

    session = _Session()
    saved, skipped = 0, 0

    try:
        for item in news_items:
            url = item["url"]
            logger.info("처리 중: %s", url)

            try:
                # 2. 뉴스 본문 크롤링
                news_content = fetch_news_content(url)
                # 3. GPT 요약 + 퀴즈 생성
                result = summarize_and_quiz(
                    news_content["title"], news_content["content"]
                )
            except Exception as e:
                logger.warning("요약 실패, 건너뜀 (%s): %s", url, e)
                skipped += 1
                continue

            quiz = result.get("quiz", {})
            options = quiz.get("options", ["", "", "", ""])

            news = News(
                section_id=section_id,
                title=result.get("title", "")[:255],
                summary=result.get("summary", "")[:1000],
                question=quiz.get("question", "")[:255],
                option1=options[0][:255] if len(options) > 0 else "",
                option2=options[1][:255] if len(options) > 1 else "",
                option3=options[2][:255] if len(options) > 2 else "",
                option4=options[3][:255] if len(options) > 3 else "",
                answer_index=quiz.get("answer_index", 0),
                explanation=quiz.get("explanation", "")[:255],
                when=_when_flag(),
                url=url[:255],
                date=datetime.now(tz=KST).strftime("%Y-%m-%d"),
            )
            session.add(news)
            saved += 1

        session.commit()
        logger.info(
            "Google News 저장 완료 (keyword='%s'): %d건 저장, %d건 건너뜀",
            keyword, saved, skipped,
        )

    except Exception:
        session.rollback()
        logger.exception("DB 저장 중 오류 발생 — 롤백 처리")
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 직접 실행
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    save_google_news("주식", section_id=200, count=5)
    save_google_news("비트코인", section_id=201, count=5)
