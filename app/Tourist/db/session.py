from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.Tourist.core.config import build_tourist_db_url

engine = create_engine(
    build_tourist_db_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
