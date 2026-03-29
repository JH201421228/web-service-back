from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.Remember.core.config import build_remember_db_url

engine = create_engine(
    build_remember_db_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
