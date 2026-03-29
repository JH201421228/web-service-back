from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.Tamagotchi.db.base import Base


class TamagotchiDailyHistory(Base):
    __tablename__ = "tamagotchi_daily_histories"
    __table_args__ = (
        UniqueConstraint("player_id", "date_key", name="uq_tamagotchi_daily_histories_player_date"),
        Index(
            "ix_tamagotchi_daily_histories_player_date",
            "player_id",
            "date_key",
        ),
        Index(
            "ix_tamagotchi_daily_histories_date_key",
            "date_key",
        ),
    )

    id = Column(Integer, primary_key=True)
    player_id = Column(
        Integer,
        ForeignKey("tamagotchi_players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date_key = Column(Date, nullable=False)
    steps = Column(Integer, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    avg_heart_rate = Column(Integer, nullable=False)
    calories = Column(Integer, nullable=False)
    active_minutes = Column(Integer, nullable=False)
    health_source = Column(String(20), nullable=False)
    score = Column(Integer, nullable=False)
    exp_gained = Column(Integer, nullable=False)
    coins_gained = Column(Integer, nullable=False)
    total_exp = Column(Integer, nullable=False)
    stage = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
