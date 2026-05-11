import json
from datetime import datetime, timedelta
from typing import Dict, Any

import ee

from app.core.config import settings

_ee_initialized = False


def _initialize_ee() -> None:
    """Initialize the Earth Engine client once.

    Try project init first, then configured service-account auth, then default auth.
    """
    global _ee_initialized
    if _ee_initialized:
        return

    try:
        ee.Initialize(project="haribon-datasets")
        print("[OK] Google Earth Engine initialized (haribon-datasets).")
        _ee_initialized = True
        return
    except Exception:
        print("Authenticating to Google Earth Engine...")

    try:
        if settings.GCP_CREDENTIALS_JSON:
            print("[GEE] Authenticating with GCP_CREDENTIALS_JSON environment variable...")
            creds_json = json.loads(settings.GCP_CREDENTIALS_JSON)
            credentials = ee.ServiceAccountCredentials(
                settings.GCP_SERVICE_ACCOUNT_EMAIL,
                key_data=json.dumps(creds_json),
            )
            ee.Initialize(credentials=credentials)
            print("[OK] GEE initialized using JSON content (Production Mode).")
            _ee_initialized = True
            return
    except Exception as exc:
        print(f"[WARN] Failed JSON-based GEE auth: {exc}")

    try:
        if settings.GCP_PRIVATE_KEY_PATH and settings.GCP_PRIVATE_KEY_PATH.exists():
            print(f"[GEE] Authenticating with key file from: {settings.GCP_PRIVATE_KEY_PATH}...")
            credentials = ee.ServiceAccountCredentials(
                settings.GCP_SERVICE_ACCOUNT_EMAIL,
                str(settings.GCP_PRIVATE_KEY_PATH),
            )
            ee.Initialize(credentials=credentials)
            print("[OK] GEE initialized using key file (Local Mode).")
            _ee_initialized = True
            return
    except Exception as exc:
        print(f"[WARN] Failed file-based GEE auth: {exc}")

    try:
        print("[WARN] No service account credentials found. Attempting default authentication...")
        ee.Initialize()
        print("[OK] GEE initialized with default credentials.")
        _ee_initialized = True
    except Exception as exc:
        print(f"[FATAL] GEE AUTHENTICATION ERROR: {exc}")

def _get_value(image, geometry, reducer=None, scale=1000, max_pixels=1e9) -> Dict[str, Any]:
    """Reduce an EE image over a geometry with basic error handling."""
    try:
        if image is None:
            return {}
        if reducer is None:
            reducer = ee.Reducer.mean()

        stats = image.reduceRegion(
            reducer=reducer,
            geometry=geometry,
            scale=scale,
            maxPixels=max_pixels,
            bestEffort=True,
            tileScale=2,
        )
        return stats.getInfo() or {}
    except Exception as exc:
        print(f"[WARN] Reduction error: {exc}")
        return {}

def get_environmental_data_for_feature(
    feature: Dict[str, Any],
    date_str: str,
    max_date_retry_days: int = 7,
) -> Dict[str, Any]:
    """Fetch operational atmospheric data for one location.

    Sources (operational/near-real-time only):
    - Precipitation: NASA GPM IMERG V07 (near-real-time, ~4h delay)
    - Wind: NOAA GFS 0.25° (operational forecast, 4x daily)
    - NDVI: Landsat 8-day composite (30m resolution)

    Marine data (SST, Salinity, Chlorophyll) comes from CMEMS service.

    If target date returns no data, retry up to max_date_retry_days earlier.
    """
    _initialize_ee()
    loc_name = feature.get("properties", {}).get("Name", "Unknown")

    if not _ee_initialized:
        print(f"[GEE] Fetching atmospheric data for {loc_name} on {date_str}")
        print("[GEE] FAIL - authentication/initialization failed")
        return {}

    try:
        geom = feature.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates")

        if not coords:
            raise ValueError("Feature has no coordinates")

        if gtype == "Point":
            point = ee.Geometry.Point(coords)
            aoi = point.buffer(5000).bounds()
        else:
            aoi = ee.Geometry.Polygon(coords)

        print(f"[GEE] Fetching atmospheric data for {loc_name} on {date_str}")

        # Try up to max_date_retry_days earlier if initial date returns empty
        attempts = [date_str]
        for retry in range(1, max_date_retry_days + 1):
            attempt_ts = datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=retry)
            attempts.append(attempt_ts.strftime("%Y-%m-%d"))

        result = {}
        for attempt_date in attempts:
            target_date = ee.Date(attempt_date)
            start_date_short = target_date.advance(-3, "day")
            start_date_medium = target_date.advance(-15, "day")

            attempt_result = {}

            # Precipitation (GPM IMERG near-real-time)
            try:
                imerg = ee.ImageCollection("NASA/GPM_L3/IMERG_V07") \
                    .filterDate(start_date_short, target_date) \
                    .filterBounds(aoi) \
                    .select("precipitation")
                
                if imerg.size().getInfo() > 0:
                    precip_img = imerg.sum()
                    precip_stats = _get_value(precip_img, aoi, scale=11000)

                    if precip_stats.get("precipitation") is not None:
                        attempt_result["Rainfall_mm"] = round(
                            precip_stats["precipitation"], 2
                        )
                        print(
                            f"  [OK] Precipitation from GPM IMERG ({attempt_date}): "
                            f"{attempt_result['Rainfall_mm']:.2f} mm"
                        )
            except Exception as exc:
                print(f"  [WARN] Precipitation error ({attempt_date}): {exc}")

            # NDVI (Landsat 8-day composite, 30m)
            try:
                ndvi_coll = ee.ImageCollection("LANDSAT/COMPOSITES/C02/T1_L2_8DAY_NDVI") \
                    .filterDate(start_date_medium, target_date) \
                    .filterBounds(aoi) \
                    .select("NDVI")
                
                if ndvi_coll.size().getInfo() > 0:
                    ndvi_img = ndvi_coll.mean()
                    ndvi_stats = _get_value(ndvi_img, aoi, scale=30)
                    if ndvi_stats.get("NDVI") is not None:
                        # Landsat NDVI is already normalized (-1 to 1)
                        attempt_result["NDVI"] = round(ndvi_stats["NDVI"], 4)
                        print(
                            f"  [OK] NDVI from Landsat 8-day ({attempt_date}): "
                            f"{attempt_result['NDVI']:.4f}"
                        )
            except Exception as exc:
                print(f"  [WARN] NDVI error ({attempt_date}): {exc}")

            # Wind (GFS operational forecast, 0.25°)
            try:
                bands_needed = [
                    "u_component_of_wind_10m_above_ground",
                    "v_component_of_wind_10m_above_ground",
                ]
                
                # APPLYING SELECT BEFORE MEAN
                gfs = ee.ImageCollection("NOAA/GFS0P25") \
                    .filterDate(start_date_short, target_date) \
                    .filterBounds(aoi) \
                    .select(bands_needed)
                
                if gfs.size().getInfo() > 0:
                    wind_img = gfs.mean() # Mean is now only calculated for the 2 bands
                    wind_stats = _get_value(wind_img, aoi, scale=27830)
                    
                    u_val = wind_stats.get("u_component_of_wind_10m_above_ground")
                    v_val = wind_stats.get("v_component_of_wind_10m_above_ground")
                    
                    if u_val is not None and v_val is not None:
                        wind_u = float(u_val)
                        wind_v = float(v_val)
                        wind_speed = (wind_u ** 2 + wind_v ** 2) ** 0.5
                        attempt_result["Wind_u_ms"] = round(wind_u, 3)
                        attempt_result["Wind_v_ms"] = round(wind_v, 3)
                        attempt_result["Wind_speed_ms"] = round(wind_speed, 3)
                        print(
                            f"  [OK] Wind from GFS ({attempt_date}): speed={wind_speed:.2f} m/s, "
                            f"u={wind_u:.2f}, v={wind_v:.2f}"
                        )
            except Exception as exc:
                print(f"  [WARN] Wind error ({attempt_date}): {exc}")

            # If we got any data, use it and stop retrying
            if attempt_result:
                result = attempt_result
                result["_fetch_date"] = attempt_date
                print(f"  [GEE] Success for {attempt_date}, stopping retry loop")
                break

        if not result:
            print(f"  [GEE] No atmospheric data available for any date in range")
            return {}

        result["data_sources"] = {
            "precipitation": "NASA GPM IMERG V07 (near-real-time, ~4h delay)",
            "ndvi": "Landsat 8-day composite (30m resolution)",
            "wind": "NOAA GFS 0.25 degree (4x daily forecast)",
        }

        print(f"  [GEE] Atmospheric data collection complete for {loc_name}")
        return result

    except Exception as exc:
        print(f"[WARN] GEE fetch failed: {type(exc).__name__}: {exc}")
        return {}
