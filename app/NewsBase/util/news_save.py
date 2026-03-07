"""
뉴스 헤드라인 수집 → 요약/퀴즈 생성 → DB 저장 스크립트

직접 실행:
    python news_save.py [section_id] [count]
    예) python news_save.py 100 5
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from datetime import datetime, timezone, timedelta

# BE 루트(alembic.ini 위치)를 Python 경로에 추가 → app.NewsBase.* import 가능
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.NewsBase.core.config import build_db_url          # noqa: E402
from app.NewsBase.models.news import News                  # noqa: E402
from app.NewsBase.util.news_headline_url import fetch_headline_urls   # noqa: E402
from app.NewsBase.util.news_summary import process_news_url           # noqa: E402

from sqlalchemy import create_engine                       # noqa: E402
from sqlalchemy.orm import sessionmaker                    # noqa: E402

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

def _when_flag() -> int:
    KST = timezone(timedelta(hours=9))
    """현재 시각 기준 오전(0) / 오후(1) 반환 (KST 기준)"""
    return 0 if datetime.now(tz=KST).hour < 12 else 1


def save_news(section_id: int = 100, count: int = 5) -> None:
    """
    section_id 섹션의 헤드라인 뉴스를 count개 가져와 DB에 저장합니다.

    Args:
        section_id : 네이버 뉴스 섹션 ID (기본 100 = 정치)
        count      : 저장할 기사 수 (기본 5)
    """
    logger.info("헤드라인 URL 수집 시작 (sid=%d, count=%d)", section_id, count)
    urls = fetch_headline_urls(sid=section_id, count=count)

    session = _Session()
    saved, skipped = 0, 0

    try:
        for url in urls:
            logger.info("처리 중: %s", url)
            try:
                result = process_news_url(url)  # {"title", "summary", "quiz": {...}}
            except Exception as e:
                logger.warning("요약 실패, 건너뜀 (%s): %s", url, e)
                skipped += 1
                continue

            quiz = result.get("quiz", {})
            options = quiz.get("options", ["", "", "", ""])

            KST = timezone(timedelta(hours=9))

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
        logger.info("저장 완료: %d건 저장, %d건 건너뜀", saved, skipped)

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
    save_news(100, 1)
