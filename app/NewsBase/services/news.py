"""
뉴스 서비스 레이어

라우터 → 서비스 → DB 순서로 호출됩니다.
"""

from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.NewsBase.models.news import News
from app.NewsBase.models.news_comment import NewsComment
from app.NewsBase.schemas.news import NewsResponse, QuizSchema


def get_news_list(db: Session, section_id: int, date: str, when: int) -> List[NewsResponse]:
    """
    섹션 ID, 날짜, 오전/오후(when) 기준으로 뉴스 목록을 DB에서 조회해 반환합니다.

    Args:
        db         : SQLAlchemy 세션 (의존성 주입)
        section_id : 네이버 뉴스 섹션 ID (100=정치, 101=경제 ...)
        date       : 조회 날짜 (YYYY-MM-DD)
        when       : 0=오전, 1=오후
    Returns:
        해당 조건에 맞는 NewsResponse 리스트
    """
    comment_count_subquery = (
        db.query(
            NewsComment.news_id.label("news_id"),
            func.count(NewsComment.comment_id).label("comment_count"),
        )
        .group_by(NewsComment.news_id)
        .subquery()
    )

    rows = (
        db.query(
            News,
            func.coalesce(comment_count_subquery.c.comment_count, 0).label("comment_count"),
        )
        .outerjoin(comment_count_subquery, comment_count_subquery.c.news_id == News.nid)
        .filter(
            News.section_id == section_id,
            News.date == date,
            News.when == when,
        )
        .order_by(News.nid.desc())
        .all()
    )

    result = []
    for row, comment_count in rows:
        result.append(
            NewsResponse(
                nid=row.nid,
                section_id=row.section_id,
                title=row.title or "",
                summary=row.summary or "",
                comment_count=int(comment_count or 0),
                quiz=QuizSchema(
                    question=row.question or "",
                    options=[
                        row.option1 or "",
                        row.option2 or "",
                        row.option3 or "",
                        row.option4 or "",
                    ],
                    answer_index=row.answer_index or 0,
                    explanation=row.explanation or "",
                ),
                when=row.when,
                url=row.url or "",
                date=row.date or "",
                created_at=row.created_at.isoformat() if row.created_at else "",
                updated_at=row.updated_at.isoformat() if row.updated_at else "",
            )
        )

    return result


def count_date_news(db: Session, date: str, when: int) -> int:
    """
    날짜 기준으로 뉴스 개수를 조회해 반환합니다.

    Args:
        db         : SQLAlchemy 세션 (의존성 주입)
        date       : 조회 날짜 (YYYY-MM-DD)
        when       : 0=오전, 1=오후
    Returns:
        해당 날짜의 뉴스 개수
    """
    return db.query(News).filter(News.date == date, News.when == when).count()
