from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.Tourist.db.base import Base


class TouristVaccinationReference(Base):
    __tablename__ = "tourist_vaccination_references"

    id = Column(Integer, primary_key=True)
    vaccine_code = Column(String(20), nullable=False, unique=True, index=True)
    vaccine_name = Column(String(255), nullable=False)
    source_key = Column(String(50), nullable=False, default="vaccination_reference")
    synced_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
