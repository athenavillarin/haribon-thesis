from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

import pandas as pd

_BASELINE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "task_1"
    / "task1_data"
    / "Task1_Combined_Baseline_Daily.csv"
)

_LOCATION_MAP = {
    "Gigantes Islands": "Gigantes Polygon",
    "Roxas City": "Roxas Polygon",
}

_BASELINE_DF: Optional[pd.DataFrame] = None


def _load_baseline_df() -> Optional[pd.DataFrame]:
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
    except Exception:
        return None


def get_copernicus_fallback_for_location(location_name: str, date_str: str) -> Dict[str, Any]:
    """Return Copernicus-derived fallback values for one location/date.

    This service reads Task 1 baseline data (already extracted from Copernicus).
    It returns the nearest available row for the mapped site.
    """
    df = _load_baseline_df()
    if df is None:
        return {}

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
        "NDVI_raw",
        "uo",
        "vo",
        "mlotst",
        "no3",
        "po4",
        "o2",
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

    out["_source"] = "copernicus_baseline"
    out["_source_date"] = str(pd.to_datetime(row["Date"]).date())
    out["_source_location"] = mapped_location
    return out
