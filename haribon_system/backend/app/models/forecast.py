from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class DailyForecast(Base):

    __tablename__ = "daily_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(Date, index=True, nullable=False)
    system_version = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DailyForecast date={self.forecast_date} version={self.system_version}>"


class Location(Base):
    __tablename__ = "location"

    location_id = Column(Integer, primary_key=True, index=True)
    location_name = Column(Text, unique=True, nullable=False)

    # Relationships
    historical_data = relationship("HistoricalData", back_populates="location", cascade="all, delete-orphan")
    prediction_logs = relationship("PredictionLog", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Location id={self.location_id} name={self.location_name}>"


class HistoricalData(Base):
    __tablename__ = "historical_data"

    record_id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    redtide_present = Column(Boolean)
    sst = Column(Float)
    chlorophyll_a_proxy = Column(Float)
    rainfall_mm = Column(Float)
    salinity = Column(Float)
    agriculture_pct = Column(Float)

    # Relationships
    location = relationship("Location", back_populates="historical_data")

    def __repr__(self) -> str:
        return f"<HistoricalData location_id={self.location_id} date={self.date} redtide={self.redtide_present}>"


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    prediction_id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)
    sst = Column(Float)
    chlorophyll_a_proxy = Column(Float)
    rainfall_mm = Column(Float)
    salinity = Column(Float)
    agriculture_pct = Column(Float)
    risk_level = Column(Text)
    confidence_score = Column(Float)

    # Relationships
    location = relationship("Location", back_populates="prediction_logs")

    def __repr__(self) -> str:
        return f"<PredictionLog location_id={self.location_id} timestamp={self.prediction_timestamp} risk={self.risk_level}>"
