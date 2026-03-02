from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.NewsBase.db.base import Base


class User(Base):
    """사용자 테이블"""
    
    __tablename__ = "users"

    uid = Column(String(128), primary_key=True, comment="Firebase UID")
    email = Column(String(255), nullable=True, index=True, comment="이메일")
    name = Column(String(100), nullable=True, comment="이름")
    picture = Column(String(500), nullable=True, comment="프로필 이미지 URL")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정일시",
    )

    def __repr__(self):
        return f"<User(uid={self.uid}, email={self.email})>"