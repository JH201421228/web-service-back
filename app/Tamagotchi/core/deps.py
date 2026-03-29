from typing import Generator

from sqlalchemy.orm import Session

from app.Tamagotchi.db.session import SessionLocal


def get_tamagotchi_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
