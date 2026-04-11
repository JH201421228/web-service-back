from typing import Generator
from sqlalchemy.orm import Session
from app.Reaper.db.session import SessionLocal


def get_reaper_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
