from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.Tourist.db.base import Base


class TouristMonthlyStatistic(Base):
    __tablename__ = "tourist_monthly_statistics"
    __table_args__ = (
        UniqueConstraint(
            "metric_key",
            "base_ym",
            "segment_key",
            name="uq_tourist_monthly_statistics_metric_segment",
        ),
    )

    id = Column(Integer, primary_key=True)
    metric_key = Column(String(50), nullable=False, index=True)
    base_ym = Column(String(6), nullable=False, index=True)
    segment_key = Column(String(50), nullable=False, index=True)
    segment_label = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    previous_quantity = Column(Integer, nullable=True)
    change_rate = Column(Float, nullable=True)
    source_key = Column(String(50), nullable=False, default="tourism_statistics")
    synced_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
