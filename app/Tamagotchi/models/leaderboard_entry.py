from sqlalchemy import Column, Date, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.Tamagotchi.db.base import Base


class TamagotchiLeaderboardEntry(Base):
    __tablename__ = "tamagotchi_daily_leaderboards"
    __table_args__ = (
        UniqueConstraint(
            "date_key",
            "install_id",
            name="uq_tamagotchi_daily_leaderboards_date_install",
        ),
        Index(
            "ix_tamagotchi_daily_leaderboards_rank",
            "date_key",
            "score",
            "submitted_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    date_key = Column(Date, nullable=False, index=True)
    install_id = Column(String(128), nullable=False, index=True)
    nickname = Column(String(60), nullable=False)
    pet_name = Column(String(60), nullable=False)
    starter_id = Column(String(20), nullable=False)
    score = Column(Integer, nullable=False)
    streak = Column(Integer, nullable=False)
    stage = Column(Integer, nullable=False)
    total_exp = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
