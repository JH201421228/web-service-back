from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func

from app.NewsBase.db.base import Base


class News(Base):
    """뉴스 테이블"""
    
    __tablename__ = "news"

    nid = Column(Integer, primary_key=True, comment="뉴스 ID")
    section_id = Column(Integer, nullable=True, index=True, comment="섹션 ID")
    title = Column(String(255), nullable=True, index=True, comment="제목")
    summary = Column(String(1000), nullable=True, comment="요약")
    question = Column(String(255), nullable=True, comment="질문")
    option1 = Column(String(255), nullable=True, comment="옵션 1")
    option2 = Column(String(255), nullable=True, comment="옵션 2")
    option3 = Column(String(255), nullable=True, comment="옵션 3")
    option4 = Column(String(255), nullable=True, comment="옵션 4")
    answer_index = Column(Integer, nullable=True, comment="정답")
    explanation = Column(String(255), nullable=True, comment="설명")
    when = Column(Integer, default=0, comment="오전: 0, 오후: 1")
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정일시",
    )

    def __repr__(self):
        return f"<News(nid={self.nid}, title={self.title})>"