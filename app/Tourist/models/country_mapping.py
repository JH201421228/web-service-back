from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.Tourist.db.base import Base


class TouristCountryMapping(Base):
    __tablename__ = "tourist_country_mappings"

    id = Column(Integer, primary_key=True)
    app_country_code = Column(String(3), nullable=False, unique=True, index=True)
    iso_alpha2 = Column(String(2), nullable=False, unique=True, index=True)
    iso_alpha3 = Column(String(3), nullable=True, index=True)
    country_name = Column(String(100), nullable=False, index=True)
    country_name_en = Column(String(200), nullable=True)
    aliases_json = Column(Text, nullable=False)
    source_key = Column(String(50), nullable=False, default="travel_warning")
    is_active = Column(Boolean, nullable=False, default=True)
    synced_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
