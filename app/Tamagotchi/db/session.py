from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.Tamagotchi.core.config import build_tamagotchi_db_url

engine = create_engine(
    build_tamagotchi_db_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
