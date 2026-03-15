from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.dialects.postgresql import JSONB

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
