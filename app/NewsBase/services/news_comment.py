from typing import List

from sqlalchemy.orm import Session

from app.NewsBase.models.news import News
from app.NewsBase.models.news_comment import NewsComment
from app.NewsBase.schemas.news_comment import (
    NewsCommentCreateRequest,
    NewsCommentResponse,
)

MAX_NEWS_COMMENTS = 100


class NewsNotFoundError(Exception):
    pass


class NewsCommentLimitError(Exception):
    pass


def _ensure_news_exists(db: Session, nid: int) -> None:
    news_exists = db.query(News.nid).filter(News.nid == nid).first()
    if news_exists is None:
        raise NewsNotFoundError("해당 뉴스를 찾을 수 없습니다.")


def _to_comment_response(row: NewsComment) -> NewsCommentResponse:
    return NewsCommentResponse(
        comment_id=row.comment_id,
        news_id=row.news_id,
        content=row.content,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def get_news_comments(db: Session, nid: int) -> List[NewsCommentResponse]:
    _ensure_news_exists(db, nid)

    rows = (
        db.query(NewsComment)
        .filter(NewsComment.news_id == nid)
        .order_by(NewsComment.created_at.asc(), NewsComment.comment_id.asc())
        .all()
    )

    return [_to_comment_response(row) for row in rows]


def create_news_comment(
    db: Session,
    nid: int,
    payload: NewsCommentCreateRequest,
) -> NewsCommentResponse:
    _ensure_news_exists(db, nid)

    comment_count = db.query(NewsComment).filter(NewsComment.news_id == nid).count()
    if comment_count >= MAX_NEWS_COMMENTS:
        raise NewsCommentLimitError("댓글은 뉴스당 최대 100개까지 작성할 수 있습니다.")

    comment = NewsComment(
        news_id=nid,
        content=payload.content.strip(),
    )

    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)
    except Exception:
        db.rollback()
        raise

    return _to_comment_response(comment)
