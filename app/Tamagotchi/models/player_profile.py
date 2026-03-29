from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.sql import func

from app.Tamagotchi.db.base import Base


class TamagotchiPlayerProfile(Base):
    __tablename__ = "tamagotchi_players"

    id = Column(Integer, primary_key=True)
    install_id = Column(String(128), nullable=False, unique=True, index=True)
    language = Column(String(5), nullable=False)
    nickname = Column(String(60), nullable=False)
    pet_name = Column(String(60), nullable=False)
    starter_id = Column(String(20), nullable=False)
    exp = Column(Integer, nullable=False)
    coins = Column(Integer, nullable=False)
    mood = Column(Integer, nullable=False)
    energy = Column(Integer, nullable=False)
    cleanliness = Column(Integer, nullable=False)
    bond = Column(Integer, nullable=False)
    streak = Column(Integer, nullable=False)
    last_sync_date = Column(Date, nullable=True, index=True)
    last_health_source = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
