from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from app.Remember.db.base import Base


class RememberAttemptRecord(Base):
    __tablename__ = "remember_attempt_records"
    __table_args__ = (
        Index(
            "ix_remember_attempt_records_event_slot",
            "discipline",
            "difficulty_id",
            "achieved_at",
        ),
        Index(
            "ix_remember_attempt_records_device_slot",
            "device_id",
            "discipline",
            "difficulty_id",
            "achieved_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    public_id = Column(String(64), nullable=False, unique=True, index=True)
    device_id = Column(String(128), nullable=False, index=True)
    nickname = Column(String(60), nullable=False)
    discipline = Column(String(20), nullable=False, index=True)
    difficulty_id = Column(String(20), nullable=False, index=True)
    difficulty_label = Column(String(60), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)
    total_items = Column(Integer, nullable=False)
    correct_items = Column(Integer, nullable=False)
    summary = Column(String(255), nullable=True)
    achieved_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
