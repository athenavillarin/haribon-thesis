from fastapi import APIRouter
from datetime import datetime, timedelta
import json
from app.core.config import settings

router = APIRouter()

@router.get("/risk-summary")
def get_risk_summary():
    """Get a summary of current risk levels across all locations."""
    try:
        # Load latest forecast
        processed_dir = settings.PROCESSED_DATA_DIR
        files = sorted(processed_dir.glob("daily_forecast_*.json"), reverse=True)

        if not files:
            return {"error": "No forecast data available"}

        with open(files[0], "r") as f:
            data = json.load(f)

        # Calculate summary statistics
        risk_counts = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
        high_risk_locations = []
        total_confidence = 0

        for forecast in data.get("forecasts", []):
            risk_level = forecast["risk_level"].lower()
            if "red" in risk_level:
                risk_counts["red"] += 1
                high_risk_locations.append(forecast["location"])
            elif "orange" in risk_level:
                risk_counts["orange"] += 1
                high_risk_locations.append(forecast["location"])
            elif "yellow" in risk_level:
                risk_counts["yellow"] += 1
            else:
                risk_counts["green"] += 1

            confidence = float(forecast["confidence"].replace("%", ""))
            total_confidence += confidence

        num_locations = len(data.get("forecasts", []))
        avg_confidence = total_confidence / num_locations if num_locations > 0 else 0

        return {
            "timestamp": data.get("last_updated"),
            "total_locations": num_locations,
            "risk_distribution": risk_counts,
            "high_risk_locations": high_risk_locations,
            "average_confidence": round(avg_confidence, 1),
            "system_status": "active"
        }

    except Exception as e:
        return {"error": f"Failed to generate summary: {str(e)}"}

@router.get("/environmental-overview")
def get_environmental_overview():
    """Get overview of current environmental conditions."""
    try:
        processed_dir = settings.PROCESSED_DATA_DIR
        files = sorted(processed_dir.glob("daily_forecast_*.json"), reverse=True)

        if not files:
            return {"error": "No forecast data available"}

        with open(files[0], "r") as f:
            data = json.load(f)

        # Aggregate environmental data
        env_summary = {
            "avg_chlorophyll": 0,
            "avg_temperature": 0,
            "avg_salinity": 0,
            "total_precipitation": 0,
            "locations_with_data": 0
        }

        count = 0
        for forecast in data.get("forecasts", []):
            env_data = forecast.get("environmental_data", {})
            if env_data.get("CHL") is not None:
                env_summary["avg_chlorophyll"] += env_data["CHL"]
                count += 1
            if env_data.get("thetao") is not None:
                env_summary["avg_temperature"] += env_data["thetao"]
            if env_data.get("so") is not None:
                env_summary["avg_salinity"] += env_data["so"]
            if env_data.get("precip_mm_day") is not None:
                env_summary["total_precipitation"] += env_data["precip_mm_day"]

        if count > 0:
            env_summary["avg_chlorophyll"] /= count
            env_summary["avg_temperature"] /= count
            env_summary["avg_salinity"] /= count

        env_summary["locations_with_data"] = count

        return {
            "timestamp": data.get("last_updated"),
            "environmental_summary": env_summary,
            "data_quality": "good" if count > 0 else "insufficient"
        }

    except Exception as e:
        return {"error": f"Failed to generate environmental overview: {str(e)}"}