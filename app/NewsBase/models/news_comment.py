from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.NewsBase.db.base import Base


class NewsComment(Base):
    """뉴스 댓글 테이블"""

    __tablename__ = "news_comments"

    comment_id = Column(Integer, primary_key=True, comment="댓글 ID")
    news_id = Column(
        Integer,
        ForeignKey("news.nid", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="뉴스 ID",
    )
    content = Column(String(500), nullable=False, comment="댓글 내용")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="작성일시",
    )

    def __repr__(self):
        return f"<NewsComment(comment_id={self.comment_id}, news_id={self.news_id})>"
