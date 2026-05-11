from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ForecastResponse(BaseModel):
    forecasts: List[Dict[str, Any]]
    last_updated: str
    system_version: str = "v2.0"

class LocationData(BaseModel):
    id: str
    name: str
    coordinates: Dict[str, float]
    current_status: Dict[str, Any]
    today_forecast: Dict[str, Any]
    five_day_outlook: List[Dict[str, Any]]
    data_quality: Dict[str, Any]
    environmental_data: Dict[str, Any]

class SimplifiedForecastResponse(BaseModel):
    metadata: Dict[str, Any]
    locations: List[LocationData]
    summary: Dict[str, Any]