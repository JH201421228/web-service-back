from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.Tourist.db.base import Base


class TouristDataSource(Base):
    __tablename__ = "tourist_data_sources"

    id = Column(Integer, primary_key=True)
    source_key = Column(String(50), nullable=False, unique=True, index=True, comment="소스 키")
    display_order = Column(Integer, nullable=False, default=0, comment="정렬 순서")
    label = Column(String(200), nullable=False, comment="표시명")
    organization = Column(String(100), nullable=False, comment="기관명")
    url = Column(String(1000), nullable=False, comment="원본 URL")
    note = Column(String(500), nullable=False, comment="설명")
    status = Column(String(20), nullable=False, default="pending", comment="동기화 상태")
    item_count = Column(Integer, nullable=False, default=0, comment="적재 건수")
    last_error = Column(Text, nullable=True, comment="마지막 오류")
    last_synced_at = Column(DateTime, nullable=True, comment="마지막 동기화 시각")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="생성 일시")
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시",
    )
