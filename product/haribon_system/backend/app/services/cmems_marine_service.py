"""
Copernicus Marine Environment Monitoring Service (CMEMS) integration.

Fetches live marine data (SST, salinity, chlorophyll, MLD, currents, nutrients)
from CMEMS via copernicusmarine library. Falls back to baseline CSV if unavailable.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

import pandas as pd

from app.core.config import settings

# Define CMEMS products and parameters to fetch
CMEMS_PRODUCTS_CONFIG = {
    "thetao": {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        "variables": ["thetao"],
        "output_key": "thetao",
        "unit": "°C",
    },
    "so": {
        "dataset_id": "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
        "variables": ["so"],
        "output_key": "so",
        "unit": "PSU",
    },
    "currents": {
        "dataset_id": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
        "variables": ["uo", "vo"],
        "output_key": "currents",
        "unit": "m/s",
    },
    "mixed_layer": {
        "dataset_id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
        "variables": ["mlotst"],
        "output_key": "mlotst",
        "unit": "m",
    },
    "chlorophyll": {
        "dataset_id": "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D",
        "variables": ["CHL"],
        "output_key": "CHL",
        "unit": "mg/m³",
    },
}

_BASELINE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "task_1"
    / "task1_data"
    / "Task1_Combined_Baseline_Daily.csv"
)

_BASELINE_DF: Optional[pd.DataFrame] = None


def _load_baseline_df() -> Optional[pd.DataFrame]:
    """Load and cache baseline data for fallback."""
    global _BASELINE_DF
    if _BASELINE_DF is not None:
        return _BASELINE_DF

    if not _BASELINE_PATH.exists():
        return None

    try:
        df = pd.read_csv(_BASELINE_PATH)
        if "Date" not in df.columns or "Location_Name" not in df.columns:
            return None
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date", "Location_Name"]).copy()
        _BASELINE_DF = df
        return _BASELINE_DF
    except Exception as e:
        print(f"[CMEMS] Failed to load baseline data: {e}")
        return None


def _fetch_cmems_data(
    dataset_id: str,
    variables: list,
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
    date_str: str,
    max_date_retry_days: int = 7,
) -> Optional[Dict[str, Any]]:
    """Fetch data from CMEMS using copernicusmarine library.
    
    If target date returns no data, retry up to max_date_retry_days earlier to find latest available.
    """
    try:
        import copernicusmarine

        if not settings.COPERNICUSMARINE_SERVICE_USERNAME or not settings.COPERNICUSMARINE_SERVICE_PASSWORD:
            return None

        # Compute date range (today ± 1 day for flexibility)
        target_date = pd.to_datetime(date_str)
        start_date = target_date - timedelta(days=1)
        end_date = target_date + timedelta(days=1)

        print(f"  [CMEMS] Requesting {dataset_id}: {start_date.date()} to {end_date.date()}")

        # Try up to max_date_retry_days earlier if initial date returns empty
        attempts = [date_str]
        for retry in range(1, max_date_retry_days + 1):
            attempts.append((pd.to_datetime(date_str) - timedelta(days=retry)).strftime('%Y-%m-%d'))
        
        result = None
        for attempt_date in attempts:
            attempt_ts = pd.to_datetime(attempt_date)
            attempt_start = attempt_ts - timedelta(days=1)
            attempt_end = attempt_ts + timedelta(days=1)
            
            print(f"  [CMEMS] Attempting {dataset_id} for {attempt_date}")
            
            # First try to open the dataset without variable filter so we can inspect
            # actual variable short names (ARCO split datasets expose different names).
            try:
                ds = copernicusmarine.open_dataset(
                    dataset_id=dataset_id,
                    username=settings.COPERNICUSMARINE_SERVICE_USERNAME,
                    password=settings.COPERNICUSMARINE_SERVICE_PASSWORD,
                    start_datetime=attempt_start.isoformat(),
                    end_datetime=attempt_end.isoformat(),
                    minimum_longitude=lon_min,
                    maximum_longitude=lon_max,
                    minimum_latitude=lat_min,
                    maximum_latitude=lat_max,
                )

                # Discover available variable names
                if hasattr(ds, "data_vars"):
                    available_vars = list(ds.data_vars.keys())
                elif isinstance(ds, dict):
                    available_vars = list(ds.keys())
                else:
                    # best-effort fallback
                    available_vars = []

                # Map requested variables to available ones (case-insensitive match)
                variables_to_use = []
                lowered = {v.lower(): v for v in available_vars}
                for req in variables:
                    if req in available_vars:
                        variables_to_use.append(req)
                    elif req.lower() in lowered:
                        variables_to_use.append(lowered[req.lower()])

                # If we discovered variables, extract means directly from ds
                attempt_result = {}
                if variables_to_use:
                    for var in variables_to_use:
                        try:
                            arr = ds[var]
                            # xarray.DataArray has .values
                            if hasattr(arr, "values"):
                                data = arr.values
                            else:
                                # dict-like
                                data = arr

                            import numpy as _np

                            flat = _np.asarray(data).ravel()
                            if flat.size > 0:
                                attempt_result[var] = float(_np.nanmean(flat))
                        except Exception:
                            # continue to next variable
                            continue

                    if attempt_result:
                        print(f"  [CMEMS] Success for {attempt_date}")
                        result = attempt_result
                        break

            except Exception as open_err:
                # If open_dataset fails, fall back to subset() below
                print(f"  [CMEMS] open_dataset inspect failed: {type(open_err).__name__}")

        # If open_dataset succeeded for any attempt date, return it
        if result:
            return result
        
        # If inspection didn't yield variables, attempt subset() with the requested names
        # Try most recent attempt date in subset mode as well
        try:
            dataset = copernicusmarine.subset(
                dataset_id=dataset_id,
                username=settings.COPERNICUSMARINE_SERVICE_USERNAME,
                password=settings.COPERNICUSMARINE_SERVICE_PASSWORD,
                start_datetime=start_date.isoformat(),
                end_datetime=end_date.isoformat(),
                minimum_longitude=lon_min,
                maximum_longitude=lon_max,
                minimum_latitude=lat_min,
                maximum_latitude=lat_max,
                variables=variables,
            )

            # Extract means for the requested variables
            result = {}
            for var in variables:
                if var in dataset:
                    try:
                        data = dataset[var].values
                    except Exception:
                        data = dataset[var]
                    import numpy as _np

                    flat = _np.asarray(data).ravel()
                    if flat.size > 0:
                        result[var] = float(_np.nanmean(flat))

            return result if result else None
        except Exception as subset_err:
            print(f"  [CMEMS] subset() also failed: {type(subset_err).__name__}")
            return None

    except Exception as e:
        print(f"[WARN] CMEMS fetch failed for {dataset_id}: {type(e).__name__}")
        return None


def get_cmems_data_for_location(
    location_name: str, coordinates: tuple, date_str: str
) -> Dict[str, Any]:
    """
    Fetch CMEMS marine data for a location and date.

    Args:
        location_name: Name of the location
        coordinates: (lon, lat) tuple
        date_str: Date string (YYYY-MM-DD)

    Returns:
        Dictionary with marine parameters and metadata.
        Falls back to baseline if CMEMS unavailable.
    """
    if not coordinates or len(coordinates) < 2:
        return {}

    lon, lat = coordinates[0], coordinates[1]
    # Small buffer around the point
    lon_min, lon_max = lon - 0.5, lon + 0.5
    lat_min, lat_max = lat - 0.5, lat + 0.5

    print(f"[CMEMS] Fetching data for {location_name} on {date_str}")

    result: Dict[str, Any] = {}
    cmems_success = False

    # Try to fetch each product
    for product_key, product_cfg in CMEMS_PRODUCTS_CONFIG.items():
        data = _fetch_cmems_data(
            dataset_id=product_cfg["dataset_id"],
            variables=product_cfg["variables"],
            lon_min=lon_min,
            lon_max=lon_max,
            lat_min=lat_min,
            lat_max=lat_max,
            date_str=date_str,
        )

        if data:
            if product_key == "currents":
                if "uo" in data:
                    result["uo"] = data["uo"]
                if "vo" in data:
                    result["vo"] = data["vo"]
            else:
                output_key = product_cfg["output_key"]
                if output_key in data:
                    result[output_key] = data[output_key]
            cmems_success = True

    if not cmems_success:
        print(f"[CMEMS] Unavailable for {location_name}; falling back to baseline.")
        return _get_baseline_fallback(location_name, date_str)

    # Tag the result
    result["_source"] = "cmems_live"
    result["_source_group"] = "Marine Hydrodynamics and Biogeochemistry (CMES)"
    result["_source_parameters"] = [
        "thetao",
        "so",
        "CHL",
        "mlotst",
        "uo",
        "vo",
    ]
    result["_source_date"] = date_str
    result["_source_location"] = location_name
    result["_fetch_status"] = "OK"

    return result


def _get_baseline_fallback(location_name: str, date_str: str) -> Dict[str, Any]:
    """Fallback to baseline CSV when CMEMS is unavailable."""
    df = _load_baseline_df()
    if df is None:
        return {}

    _LOCATION_MAP = {
        "Gigantes Islands": "Gigantes Polygon",
        "Roxas City": "Roxas Polygon",
    }

    mapped_location = _LOCATION_MAP.get(location_name)
    if not mapped_location:
        return {}

    loc_df = df[df["Location_Name"] == mapped_location].copy()
    if loc_df.empty:
        return {}

    try:
        target_date = pd.to_datetime(date_str)
    except Exception:
        target_date = datetime.utcnow()

    loc_df["date_diff"] = (loc_df["Date"] - target_date).abs()
    row = loc_df.sort_values("date_diff").iloc[0]

    keys = [
        "CHL",
        "thetao",
        "so",
        "precip_mm_day",
        "wind_speed_ms",
        "wind_u_ms",
        "wind_v_ms",
        "NDVI_daily",
        "uo",
        "vo",
        "mlotst",
        "no3",
        "po4",
    ]

    out: Dict[str, Any] = {}
    for key in keys:
        if key not in row.index:
            continue
        val = row[key]
        if pd.isna(val):
            continue
        out[key] = float(val)

    if not out:
        return {}

    out["_source"] = "baseline_fallback"
    out["_source_group"] = "Marine Hydrodynamics and Biogeochemistry (CMES)"
    out["_source_parameters"] = ["CHL", "thetao", "so", "mlotst", "uo", "vo"]
    out["_source_date"] = str(pd.to_datetime(row["Date"]).date())
    out["_source_location"] = mapped_location
    out["_fetch_status"] = "BASELINE"

    return out
