from pathlib import Path
import json
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.config import settings
from app.core.schemas import ForecastResponse, SimplifiedForecastResponse
import pandas as pd
import joblib
from ml_xgboost.inference_script import predict_risk, create_inference_features

router = APIRouter()


def _normalize_location_key(value: str) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _resolve_historical_dataset_path() -> Path:
    candidates = [
        settings.TRAINING_DATA_PATH,
        settings.BASE_DIR.parent / "final_compiled_dataset" / "Combined_Labeled.csv",
        settings.BASE_DIR.parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Unable to locate Combined_Labeled.csv. Tried: "
        + ", ".join(str(path) for path in candidates)
    )

def _load_latest_forecast_data():
    """Helper to load today's processed forecast file. If not found, load the most recent one."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    filepath = settings.PROCESSED_DATA_DIR / f"daily_forecast_{today_str}.json"
    
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
            
    # Fallback: Find the most recent file
    try:
        files = list(settings.PROCESSED_DATA_DIR.glob("daily_forecast_*.json"))
        if not files:
            raise FileNotFoundError("No forecast files found")
            
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Forecast not found. The daily update script may not have run yet."
        )

def _simplify_forecast_for_frontend(raw_data):
    """Convert complex forecast data to frontend-friendly format."""
    simplified = {
        "metadata": {
            "last_updated": raw_data.get("last_updated"),
            "system_version": raw_data.get("system_version", "v2.0"),
            "total_locations": len(raw_data.get("forecasts", [])),
            "forecast_date": raw_data.get("forecasts", [{}])[0].get("date") if raw_data.get("forecasts") else None
        },
        "locations": [],
        "summary": {
            "risk_distribution": {"green": 0, "yellow": 0, "orange": 0, "red": 0},
            "average_confidence": 0,
            "high_risk_locations": [],
            "data_quality_avg": 0
        }
    }

    total_confidence = 0
    total_quality = 0

    for forecast in raw_data.get("forecasts", []):
        # Simplified location data
        location_data = {
            "id": forecast["location"].lower().replace(" ", "_"),
            "name": forecast["location"],
            "coordinates": {
                "lat": forecast["latitude"],
                "lng": forecast["longitude"]
            },
            # Flattened properties for frontend compatibility
            "risk_level": forecast["risk_level"],
            "risk_color": _get_risk_color(forecast["risk_level"]),
            "confidence": forecast["confidence"],
            
            "current_status": {
                "risk_level": forecast["risk_level"],
                "risk_color": _get_risk_color(forecast["risk_level"]),
                "confidence": forecast["confidence"],
                "safe_to_harvest": "Green" in forecast["risk_level"]
            },
            "today_forecast": {
                "probability": forecast["red_tide_probability"],
                "recommendations": forecast["recommendations"],
                "contributing_factors": forecast["contributing_factors"]
            },
            "five_day_outlook": [],
            "data_quality": {
                "score": forecast.get("data_quality", {}).get("quality_score", 0),
                "confidence_level": forecast.get("data_quality", {}).get("confidence_level", "Medium"),
                "warnings": forecast.get("data_quality", {}).get("warnings", [])
            },
            "environmental_data": forecast.get("environmental_data", {})
        }

        # Simplified 5-day forecast
        # First entry: Today (using current prediction)
        location_data["five_day_outlook"].append({
            "day": "Today",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "label": "Today",
            "risk_level": forecast["risk_level"], # Main "today" risk
            "risk_color": _get_risk_color(forecast["risk_level"]),
            "confidence": forecast["confidence"],
            "probability": forecast["red_tide_probability"]
        })
        
        # Subsequent entries: Future forecast
        if "five_day_forecast" in forecast:
            for day_forecast in forecast["five_day_forecast"]:
                day_data = {
                    "day": day_forecast["forecast_day"],
                    "date": day_forecast["date"],
                    "label": day_forecast["day_label"],
                    "risk_level": day_forecast["risk_level"],
                    "risk_color": _get_risk_color(day_forecast["risk_level"]),
                    "confidence": day_forecast["confidence"],
                    "probability": day_forecast["probability"]
                }
                location_data["five_day_outlook"].append(day_data)
        
        # Limit to 5 items total if needed, or keep all
        location_data["five_day_outlook"] = location_data["five_day_outlook"][:5]

        simplified["locations"].append(location_data)

        # Update summary statistics
        risk_key = _get_risk_key(forecast["risk_level"])
        simplified["summary"]["risk_distribution"][risk_key] += 1

        confidence_val = float(forecast["confidence"].replace("%", ""))
        total_confidence += confidence_val

        quality_score = forecast.get("data_quality", {}).get("quality_score", 0)
        total_quality += quality_score

        risk_text = (forecast.get("risk_level") or "").lower()
        if (
            "red" in risk_text
            or "orange" in risk_text
            or "high" in risk_text
            or "moderate" in risk_text
        ):
            simplified["summary"]["high_risk_locations"].append(forecast["location"])

    # Calculate averages
    num_locations = len(simplified["locations"])
    if num_locations > 0:
        simplified["summary"]["average_confidence"] = round(total_confidence / num_locations, 1)
        simplified["summary"]["data_quality_avg"] = round(total_quality / num_locations, 1)

    return simplified

def _get_risk_color(risk_level):
    """Map risk level to color for frontend."""
    normalized = (risk_level or "").lower()
    if "red" in normalized or "high" in normalized:
        return "red"
    elif "orange" in normalized or "moderate" in normalized:
        return "orange"
    elif "yellow" in normalized or "low" in normalized:
        return "yellow"
    else:
        return "green"

def _get_risk_key(risk_level):
    """Map risk level to summary key."""
    normalized = (risk_level or "").lower()
    if "red" in normalized or "high" in normalized:
        return "red"
    elif "orange" in normalized or "moderate" in normalized:
        return "orange"
    elif "yellow" in normalized or "low" in normalized:
        return "yellow"
    else:
        return "green"


@router.post("/update")
def trigger_daily_update(background_tasks: BackgroundTasks):
    """Trigger the daily updater to regenerate today's forecast in the background."""
    try:
        from app.scripts.daily_updater import run_daily_update_with_5day_forecast
        background_tasks.add_task(run_daily_update_with_5day_forecast)
        return {"status": "started", "message": "Daily forecast update initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start daily update: {e}")


@router.post("/trigger-update")
def trigger_daily_update_compat(background_tasks: BackgroundTasks):
    """Compatibility endpoint used by the frontend to refresh data.

    Delegates to the same daily updater as /update so older frontend
    code calling /api/forecast/trigger-update continues to work.
    """
    return trigger_daily_update(background_tasks)

@router.get("/today", response_model=ForecastResponse)
def get_full_forecast():
    """Serves the pre-generated forecast for today for all monitored locations."""
    return _load_latest_forecast_data()

@router.get("/latest")
def get_simplified_forecast():
    """Serves a simplified, frontend-friendly version of today's forecast."""
    raw_data = _load_latest_forecast_data()
    return _simplify_forecast_for_frontend(raw_data)

@router.get("/locations")
def get_locations_summary():
    """Get just the location names and current risk levels."""
    raw_data = _load_latest_forecast_data()
    locations = []

    for forecast in raw_data.get("forecasts", []):
        locations.append({
            "id": forecast["location"].lower().replace(" ", "_"),
            "name": forecast["location"],
            "risk_level": forecast["risk_level"],
            "risk_color": _get_risk_color(forecast["risk_level"]),
            "confidence": forecast["confidence"],
            "coordinates": {
                "lat": forecast["latitude"],
                "lng": forecast["longitude"]
            }
        })

    return {
        "locations": locations,
        "last_updated": raw_data.get("last_updated"),
        "total_count": len(locations)
    }

@router.get("/location/{location_name}")
def get_location_detail(location_name: str):
    """Get detailed forecast for a specific location."""
    raw_data = _load_latest_forecast_data()

    # Find the location (case-insensitive)
    target_location = None
    for forecast in raw_data.get("forecasts", []):
        if forecast["location"].lower().replace(" ", "_") == location_name.lower():
            target_location = forecast
            break

    if not target_location:
        raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found")

    simplified = _simplify_forecast_for_frontend({"forecasts": [target_location]})
    return simplified["locations"][0] if simplified["locations"] else {}

@router.get("/latest")
def get_latest_forecast():
    """Get the most recent forecast file available."""
    processed_dir = settings.PROCESSED_DATA_DIR
    files = sorted(processed_dir.glob("daily_forecast_*.json"), reverse=True)

    if not files:
        raise HTTPException(status_code=404, detail="No forecast file found")

    with open(files[0], "r") as f:
        data = json.load(f)
    return data

@router.get("/predict/{location_name}")
def get_live_prediction(location_name: str):
    """Get a live prediction for a specific location using current environmental data."""
    try:
        # Load historical data for context
        historical_data = pd.read_csv(settings.TRAINING_DATA_PATH)
        historical_data['Date'] = pd.to_datetime(historical_data['Date'])

        # Load ML model artifacts
        model_path = settings.ML_DIR / 'haribon_model_v2.joblib'
        scaler_path = settings.ML_DIR / 'haribon_scaler_v2.joblib'
        features_path = settings.ML_DIR / 'haribon_feature_names_v2.txt'

        if not all(p.exists() for p in [model_path, scaler_path, features_path]):
            raise HTTPException(status_code=503, detail="ML model not trained yet. Please run training first.")

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        with open(features_path, 'r') as f:
            feature_names = [line.strip() for line in f.readlines()]

        # Get latest data for the location
        location_data = historical_data[historical_data['Location_Name'] == location_name]
        if location_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for location '{location_name}'")

        latest_data = location_data.sort_values('Date').iloc[-1:].copy()

        # Make prediction
        prediction = predict_risk(
            latest_data.to_dict('records')[0],
            historical_data,
            model,
            scaler,
            feature_names
        )

        return {
            "location": location_name,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat(),
            "model_version": "v2.0"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/historical/{location_name}")
def get_historical_data(
    location_name: str,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Return historical red-tide alerts for charts (monthly bars + timeline)."""
    try:
        historical_data = pd.read_csv(_resolve_historical_dataset_path())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load historical data: {exc}")

    if historical_data.empty:
        return {
            "location": location_name,
            "monthly_alerts": [],
            "timeline": [],
            "available_range": None,
        }

    historical_data["Date"] = pd.to_datetime(historical_data["Date"], errors="coerce")
    historical_data = historical_data.dropna(subset=["Date"])
    historical_data["red_tide_label"] = pd.to_numeric(historical_data["red_tide_label"], errors="coerce").fillna(0.0)

    if historical_data.empty:
        return {
            "location": location_name,
            "monthly_alerts": [],
            "timeline": [],
            "available_range": None,
        }

    normalized_request = _normalize_location_key(location_name)
    selected_df = historical_data
    resolved_location = "all"

    if normalized_request not in {"all", ""}:
        names = historical_data["Location_Name"].dropna().unique().tolist()
        name_map = {_normalize_location_key(name): name for name in names}
        matched_name = name_map.get(normalized_request)

        if matched_name is None:
            alt_match = location_name.replace("_", " ").strip().lower()
            for name in names:
                if name.lower() == alt_match:
                    matched_name = name
                    break

        if matched_name is None:
            raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found in historical dataset")

        resolved_location = matched_name
        selected_df = historical_data[historical_data["Location_Name"] == matched_name]

    if from_date:
        start_dt = pd.to_datetime(from_date, errors="coerce")
        if pd.isna(start_dt):
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
        selected_df = selected_df[selected_df["Date"] >= start_dt]

    if to_date:
        end_dt = pd.to_datetime(to_date, errors="coerce")
        if pd.isna(end_dt):
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        selected_df = selected_df[selected_df["Date"] <= end_dt]

    if selected_df.empty:
        return {
            "location": resolved_location,
            "monthly_alerts": [],
            "timeline": [],
            "available_range": {
                "start": historical_data["Date"].min().strftime("%Y-%m-%d"),
                "end": historical_data["Date"].max().strftime("%Y-%m-%d"),
            },
        }

    # Red-tide event threshold from the binary label.
    selected_df = selected_df.copy()
    selected_df["is_alert"] = (selected_df["red_tide_label"] >= 0.5).astype(int)

    monthly_counts = (
        selected_df
        .groupby(selected_df["Date"].dt.to_period("M"))["is_alert"]
        .sum()
        .reset_index(name="value")
    )
    monthly_counts["label"] = monthly_counts["Date"].astype(str)

    timeline_counts = (
        selected_df
        .groupby(selected_df["Date"].dt.date)["is_alert"]
        .sum()
        .reset_index(name="value")
    )
    timeline_counts["date"] = timeline_counts["Date"].astype(str)

    return {
        "location": resolved_location,
        "monthly_alerts": monthly_counts[["label", "value"]].to_dict("records"),
        "timeline": timeline_counts[["date", "value"]].to_dict("records"),
        "available_range": {
            "start": historical_data["Date"].min().strftime("%Y-%m-%d"),
            "end": historical_data["Date"].max().strftime("%Y-%m-%d"),
        },
    }