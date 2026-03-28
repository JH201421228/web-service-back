from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.Tourist.db.base import Base


class TouristCountrySnapshot(Base):
    __tablename__ = "tourist_country_snapshots"

    id = Column(Integer, primary_key=True)
    country_code = Column(String(3), nullable=False, unique=True, index=True, comment="ISO 코드")
    country_name = Column(String(100), nullable=False, index=True, comment="국가명")
    country_name_en = Column(String(200), nullable=True, comment="영문 국가명")
    continent = Column(String(60), nullable=True, comment="대륙/지역")
    flag_image_url = Column(String(1000), nullable=True, comment="국기 이미지 URL")
    map_image_url = Column(String(1000), nullable=True, comment="위험지도 이미지 URL")
    alert_level = Column(String(20), nullable=False, default="none", index=True, comment="대표 경보 단계")
    alert_summary = Column(String(500), nullable=True, comment="대표 경보 요약")
    attention = Column(String(50), nullable=True, comment="여행유의")
    attention_partial = Column(String(50), nullable=True, comment="여행유의 일부")
    attention_note = Column(Text, nullable=True, comment="여행유의 내용")
    control = Column(String(50), nullable=True, comment="여행자제")
    control_partial = Column(String(50), nullable=True, comment="여행자제 일부")
    control_note = Column(Text, nullable=True, comment="여행자제 내용")
    limita = Column(String(50), nullable=True, comment="출국권고")
    limita_partial = Column(String(50), nullable=True, comment="출국권고 일부")
    limita_note = Column(Text, nullable=True, comment="출국권고 내용")
    ban = Column(String(50), nullable=True, comment="여행금지")
    ban_partial = Column(String(50), nullable=True, comment="여행금지 일부")
    ban_note = Column(Text, nullable=True, comment="여행금지 내용")
    entry_requirement = Column(Text, nullable=True, comment="입국허가요건 요약")
    entry_requirement_details = Column(Text, nullable=True, comment="입국허가요건 상세 JSON")
    quarantine_summary = Column(String(500), nullable=True, comment="검역 정보 요약")
    quarantine_diseases = Column(Text, nullable=True, comment="검역 감염병 목록 JSON")
    source_updated_at = Column(String(50), nullable=True, comment="원천 데이터 기준일")
    synced_at = Column(DateTime, server_default=func.now(), nullable=False, comment="동기화 일시")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="생성 일시")
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시",
    )
