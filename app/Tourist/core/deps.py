from typing import Generator

from sqlalchemy.orm import Session

from app.Tourist.db.session import SessionLocal


def get_tourist_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
