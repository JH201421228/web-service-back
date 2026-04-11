from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.Reaper.db.base import Base


class ReaperGame(Base):
    __tablename__ = "reaper_games"

    id = Column(String(36), primary_key=True)
    title = Column(String(100), nullable=False)
    creator_uid = Column(String(128), nullable=False)
    status = Column(String(20), default="waiting")
    player_capacity = Column(Integer, default=6)
    bot_total = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    winner = Column(String(20), nullable=True)

    players = relationship("ReaperPlayer", back_populates="game", cascade="all, delete-orphan")


class ReaperPlayer(Base):
    __tablename__ = "reaper_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(36), ForeignKey("reaper_games.id"), nullable=False)
    uid = Column(String(128), nullable=False)
    nickname = Column(String(50), nullable=False)
    hashtag = Column(String(10), nullable=False)
    is_bot = Column(Boolean, default=False)
    seat_number = Column(Integer, nullable=False)
    role = Column(String(20), nullable=True)
    is_alive = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    grim_score = Column(Integer, default=50)
    power_score = Column(Integer, default=20)
    influence_score = Column(Integer, default=30)
    threat_score = Column(Integer, default=20)

    game = relationship("ReaperGame", back_populates="players")
