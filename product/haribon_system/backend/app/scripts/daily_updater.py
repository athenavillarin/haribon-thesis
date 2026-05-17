import json
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import Date
from typing import Optional
from types import SimpleNamespace
from functools import lru_cache

def _discover_repo_root(start_path: Path) -> Path:
    current = start_path.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "artifacts" / "THESIS_WINNERS.json").exists():
            return candidate
    return current.parents[4]


backend_dir = Path(__file__).resolve().parent.parent.parent
system_dir = backend_dir.parent
repo_root = _discover_repo_root(Path(__file__).resolve().parent)
project_root = repo_root

sys.path.append(str(backend_dir))
sys.path.append(str(system_dir))
sys.path.append(str(repo_root / "product" / "haribon_system"))


from app.core.config import settings, get_thesis_winners_manifest

try:
    from app.core.database import SessionLocal
    from app.models.forecast import DailyForecast, Location, PredictionLog
except Exception as db_import_error:
    SessionLocal = None
    DailyForecast = None
    Location = None
    PredictionLog = None
    print(f"[WARN] Database persistence disabled in updater: {db_import_error}")

try:
    from app.services.gee_service import get_environmental_data_for_feature
except Exception as gee_import_error:
    get_environmental_data_for_feature = None
    print(f"[WARN] GEE service unavailable; forecasts will use non-GEE fallback data: {gee_import_error}")

try:
    from app.services.cmems_marine_service import get_cmems_data_for_location
except Exception as cmems_import_error:
    get_cmems_data_for_location = None
    print(f"[WARN] CMEMS service unavailable: {cmems_import_error}")



def _get_manifest_model_path(manifest: Optional[dict]) -> Optional[Path]:
    """Return XGBoost model artifact path declared in thesis manifest, if present."""
    if not manifest:
        return None

    try:
        rel_path = (
            manifest.get("forecasting", {})
            .get("composition", {})
            .get("xgboost", {})
            .get("artifact_path")
        )
        if not rel_path:
            return None

        candidate = project_root / rel_path
        return candidate
    except Exception:
        return None


def load_ml_components(historical_df: pd.DataFrame, manifest: Optional[dict] = None):
    """Load the production XGBoost model and feature names.

    This replaces the older haribon_model_v2 + scaler pipeline and instead
    uses the tuned XGBoost model trained in xgboost_model/train_xgboost_haribon.py.
    """
    from xgboost import XGBClassifier

    default_candidates = [
        project_root / "artifacts" / "best_model" / "xgboost" / "best_xgboost_model.json",
        project_root / "thesis" / "xgboost_model" / "saved_model" / "best_xgboost_model.json",
        project_root / "thesis" / "xgboost_model" / "results" / "best_xgboost_model.json",
        project_root / "xgboost_model" / "saved_model" / "best_xgboost_model.json",
        project_root / "xgboost_model" / "results" / "best_xgboost_model.json",
    ]

    model_path = _get_manifest_model_path(manifest)
    if model_path is not None and not model_path.exists():
        print(f"[WARN] Manifest-selected model not found at {model_path}; trying defaults")
        model_path = None

    if model_path is None:
        model_path = next((p for p in default_candidates if p.exists()), default_candidates[0])

    print(f"Loading XGBoost model from {model_path}...")
    model = XGBClassifier()
    model.load_model(str(model_path))

    booster_features = getattr(model.get_booster(), "feature_names", None)
    if booster_features:
        feature_names = list(booster_features)
    else:
        feature_names = [
            col
            for col in historical_df.columns
            if col
            not in [
                "red_tide",
                "red_tide_label",
                "red_tide_binary",
                "Date",
                "Location_Name",
                "Month",
                "NDVI_raw",
            ]
        ]

    # The trained XGBoost artifact explicitly excludes NDVI_raw, so remove it even
    # if it appears in the historical dataset.
    feature_names = [col for col in feature_names if col != "NDVI_raw"]

    print(f"XGBoost feature columns ({len(feature_names)}): {feature_names}")
    return model, feature_names

def load_historical_data():
    """Load the historical dataset to direct feature engineering."""
    data_path = repo_root / "final_compiled_dataset" / "Combined_Labeled.csv"
    if not data_path.exists():
        possible_paths = [
            repo_root / "thesis" / "final_compiled_dataset" / "Combined_Labeled.csv",
            Path("final_compiled_dataset/Combined_Labeled.csv"),
            Path("../final_compiled_dataset/Combined_Labeled.csv"),
            Path("../../final_compiled_dataset/Combined_Labeled.csv"),
        ]
        for p in possible_paths:
            if p.exists():
                data_path = p
                break
    
    print(f"Loading historical data from {data_path}...")
    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def _resolve_split_num_for_date(reference_date: datetime) -> int:
    year = int(reference_date.year)
    if year <= 2020:
        return 1
    if year == 2021:
        return 2
    if year == 2022:
        return 3
    if year == 2023:
        return 4
    if year == 2024:
        return 5
    return 6


def _get_manifest_transformer_scenario(manifest: Optional[dict]) -> str:
    method = str(manifest.get("imputation", {}).get("primary_method", "") if manifest else "").lower()
    return "hybrid_adaptive" if "adaptive" in method else "native_masking"


def _ensure_ensemble_code_on_path() -> None:
    ensemble_code = repo_root / "thesis" / "ensemble_model" / "code"
    if not ensemble_code.exists():
        ensemble_code = repo_root / "ensemble_model" / "code"
    if ensemble_code.exists() and str(ensemble_code) not in sys.path:
        sys.path.insert(0, str(ensemble_code))


def _build_current_sequence_and_tab(location_df: pd.DataFrame, feature_row: dict, reference_date: datetime):
    _ensure_ensemble_code_on_path()
    from ensemble_data import FEATURES, LOOKBACK  # type: ignore

    loc = location_df.copy()
    loc = loc.sort_values("Date")
    feature_cols = [c for c in FEATURES if c in loc.columns]
    if not feature_cols:
        return None, None, []

    row = {c: feature_row.get(c, np.nan) for c in feature_cols}
    row["Date"] = pd.to_datetime(reference_date)
    appended = pd.concat([loc[["Date", *feature_cols]], pd.DataFrame([row])], ignore_index=True)

    # Keep the same robust fallback style as updater to avoid NaNs in sequence windows.
    appended[feature_cols] = appended[feature_cols].ffill().bfill()
    if appended[feature_cols].isna().any().any():
        appended[feature_cols] = appended[feature_cols].fillna(appended[feature_cols].mean())
    if appended[feature_cols].isna().any().any():
        appended[feature_cols] = appended[feature_cols].fillna(0.0)

    mat = appended[feature_cols].to_numpy(dtype=np.float32)
    if mat.shape[0] < LOOKBACK:
        pad_rows = np.repeat(mat[[0]], LOOKBACK - mat.shape[0], axis=0) if mat.shape[0] > 0 else np.zeros((LOOKBACK, len(feature_cols)), dtype=np.float32)
        mat = np.vstack([pad_rows, mat])

    window = mat[-LOOKBACK:]
    x_seq_test = np.expand_dims(window, axis=0)
    x_tab_test = np.expand_dims(window[-1], axis=0)

    # Build a lightweight train tensor for transformer normalization fallback.
    train_windows = []
    for i in range(LOOKBACK - 1, len(mat) - 1):
        train_windows.append(mat[i - LOOKBACK + 1 : i + 1])
    if train_windows:
        x_seq_train = np.stack(train_windows, axis=0).astype(np.float32)
    else:
        x_seq_train = x_seq_test.copy()

    return x_seq_train, x_seq_test, feature_cols



def _predict_weighted_avg_probability(
    manifest: Optional[dict],
    historical_df: pd.DataFrame,
    location: str,
    feature_row: dict,
    xgb_probability: float,
    reference_date: datetime,
) -> Optional[float]:
    """Return weighted average ensemble probability for one location/date, or None on failure."""
    try:
        _ensure_ensemble_code_on_path()
        from ensemble_inference import predict_gru, predict_lstm, predict_transformer  # type: ignore

        loc_df = historical_df[historical_df["Location_Name"] == location].copy()
        x_seq_train, x_seq_test, seq_feature_cols = _build_current_sequence_and_tab(
            location_df=loc_df,
            feature_row=feature_row,
            reference_date=reference_date,
        )
        if x_seq_test is None:
            return None

        split_num = _resolve_split_num_for_date(reference_date)
        split_like = SimpleNamespace(
            split_num=split_num,
            X_seq_train=x_seq_train,
            X_seq_test=x_seq_test,
            X_tab_train=np.empty((0, len(seq_feature_cols)), dtype=np.float32),
            X_tab_test=np.empty((1, len(seq_feature_cols)), dtype=np.float32),
            y_train=np.empty((0,), dtype=np.int64),
            y_test=np.array([0], dtype=np.int64),
        )

        transformer_scenario = _get_manifest_transformer_scenario(manifest)
        lstm_prob = float(predict_lstm(split_like)[0])
        gru_prob = float(predict_gru(split_like)[0])
        transformer_prob = float(predict_transformer(split_like, scenario=transformer_scenario)[0])

        # Weights proportional to AUC scores from thesis results, normalized to sum to 1
        # LSTM=0.7363, GRU=0.6990, Transformer=0.6265, XGBoost=0.7082
        total_auc = 0.7357 + 0.7000 + 0.6556 + 0.7077
        weights = {
            "lstm": 0.7357 / total_auc,
            "gru": 0.7000 / total_auc,
            "transformer": 0.6556 / total_auc,
            "xgboost": 0.7077 / total_auc,
        }

        weighted_prob = (
            lstm_prob * weights["lstm"] +
            gru_prob * weights["gru"] +
            transformer_prob * weights["transformer"] +
            float(xgb_probability) * weights["xgboost"]
        )
        return float(weighted_prob)
    except Exception as exc:
        print(f"[WARN] Weighted average ensemble inference failed, fallback to XGBoost: {exc}")
        return None

def get_latest_data_for_location(df, location_name):
    """Get the latest available data row for a specific location."""
    loc_df = df[df['Location_Name'] == location_name].sort_values('Date')
    if loc_df.empty:
        return None
    return loc_df.iloc[-1]


def _is_missing(value) -> bool:
    """Return True if value is None/NaN-like."""
    return value is None or pd.isna(value)


def _build_feature_imputation_stats(historical_df: pd.DataFrame, feature_names: list[str]):
    """Precompute climatological means used by training-time imputation logic."""
    stats_df = historical_df.copy()
    stats_df['Month'] = pd.to_datetime(stats_df['Date']).dt.month

    loc_month_means = stats_df.groupby(['Location_Name', 'Month'])[feature_names].mean()
    loc_means = stats_df.groupby('Location_Name')[feature_names].mean()
    global_means = stats_df[feature_names].mean()

    return loc_month_means, loc_means, global_means


def _build_feature_row_with_fallbacks(
    feature_names: list[str],
    source_data: dict,
    location: str,
    month: int,
    reference_date: datetime,
    historical_df: pd.DataFrame,
    loc_month_means: pd.DataFrame,
    loc_means: pd.DataFrame,
    global_means: pd.Series,
):
    """Create one model input row using a hybrid gap-type adaptive fallback strategy.

    Priority for missing values:
    1) short-gap temporal estimate from recent history
    2) climatological mean for location+month
    3) location-wide mean
    4) global mean
    """
    row = {}
    observed_non_missing = 0
    imputation_sources = {}

    loc_hist = historical_df[historical_df["Location_Name"] == location].copy()
    if not loc_hist.empty:
        loc_hist["Date"] = pd.to_datetime(loc_hist["Date"], errors="coerce")
        loc_hist = loc_hist[loc_hist["Date"].notna()]

    def _estimate_short_gap_temporal(col: str):
        if loc_hist.empty or col not in loc_hist.columns:
            return np.nan

        series = loc_hist[["Date", col]].dropna(subset=[col]).sort_values("Date")
        if series.empty:
            return np.nan

        target_ts = pd.to_datetime(reference_date)
        series = series[series["Date"] <= target_ts]
        if series.empty:
            return np.nan

        last_date = series.iloc[-1]["Date"]
        gap_days = int((target_ts.normalize() - pd.to_datetime(last_date).normalize()).days)
        if gap_days < 0 or gap_days > 14:
            return np.nan

        # For very short gaps, persistence is more stable than extrapolation.
        if gap_days <= 2:
            return series.iloc[-1][col]

        # For short/medium gaps, use a simple trend from recent observations.
        recent = series.tail(5)
        if len(recent) < 2:
            return series.iloc[-1][col]

        x = (recent["Date"] - recent["Date"].min()).dt.days.astype(float).values
        y = recent[col].astype(float).values

        if np.allclose(x, x[0]):
            return y[-1]

        slope, intercept = np.polyfit(x, y, 1)
        target_x = float((target_ts - recent["Date"].min()).days)
        est = float(intercept + slope * target_x)

        y_min = float(np.min(y))
        y_max = float(np.max(y))
        pad = 0.25 * max(abs(y_max - y_min), 1e-6)
        est = min(max(est, y_min - pad), y_max + pad)
        return est

    for col in feature_names:
        raw_val = source_data.get(col, np.nan)
        if not _is_missing(raw_val):
            row[col] = raw_val
            observed_non_missing += 1
            imputation_sources[col] = "observed"
            continue

        # Fallback 1: temporal estimate for short gaps (hybrid gap-type adaptive)
        val = np.nan
        val = _estimate_short_gap_temporal(col)
        if not _is_missing(val):
            row[col] = val
            imputation_sources[col] = "temporal_short_gap"
            continue

        # Fallback 2: climatological mean for this location+month
        if (location, month) in loc_month_means.index:
            val = loc_month_means.loc[(location, month), col]
            if not _is_missing(val):
                row[col] = val
                imputation_sources[col] = "climatological_location_month"
                continue

        # Fallback 3: location-wide mean
        if _is_missing(val) and location in loc_means.index:
            val = loc_means.loc[location, col]
            if not _is_missing(val):
                row[col] = val
                imputation_sources[col] = "climatological_location"
                continue

        # Fallback 4: global mean
        if _is_missing(val):
            val = global_means.get(col, np.nan)

        row[col] = val
        imputation_sources[col] = "climatological_global"

    return row, observed_non_missing, imputation_sources


def _select_display_value(
    col: str,
    mapped_env: dict,
    input_data: dict,
    feature_row: dict,
    latest_row: pd.Series,
):
    """Choose display value in priority order: live/fallback env, raw input, imputed row, latest historical."""
    value = mapped_env.get(col, np.nan) if mapped_env else np.nan
    if not _is_missing(value):
        return value

    value = input_data.get(col, np.nan)
    if not _is_missing(value):
        return value

    value = feature_row.get(col, np.nan)
    if not _is_missing(value):
        return value

    value = latest_row.get(col, np.nan)
    if not _is_missing(value):
        return value

    return None


def _compute_recent_red_tide_signal(
    historical_df: pd.DataFrame,
    location: str,
    reference_date: datetime,
) -> dict:
    loc_df = historical_df[historical_df["Location_Name"] == location].copy()
    if loc_df.empty or "red_tide_label" not in loc_df.columns:
        return {
            "has_signal": False,
            "days_since_last_positive": None,
            "recent_positive_rate_90d": None,
            "recent_positive_rate_365d": None,
        }

    loc_df["Date"] = pd.to_datetime(loc_df["Date"], errors="coerce")
    loc_df = loc_df.dropna(subset=["Date", "red_tide_label"])
    if loc_df.empty:
        return {
            "has_signal": False,
            "days_since_last_positive": None,
            "recent_positive_rate_90d": None,
            "recent_positive_rate_365d": None,
        }

    loc_df = loc_df[loc_df["Date"] <= pd.to_datetime(reference_date)]
    if loc_df.empty:
        return {
            "has_signal": False,
            "days_since_last_positive": None,
            "recent_positive_rate_90d": None,
            "recent_positive_rate_365d": None,
        }

    loc_df = loc_df.sort_values("Date")
    loc_df["positive"] = (loc_df["red_tide_label"] >= 0.5).astype(int)

    cutoff_90 = pd.to_datetime(reference_date) - pd.Timedelta(days=90)
    cutoff_365 = pd.to_datetime(reference_date) - pd.Timedelta(days=365)
    recent_90 = loc_df[loc_df["Date"] >= cutoff_90]
    recent_365 = loc_df[loc_df["Date"] >= cutoff_365]

    rate_90 = float(recent_90["positive"].mean()) if not recent_90.empty else None
    rate_365 = float(recent_365["positive"].mean()) if not recent_365.empty else None

    positive_rows = loc_df[loc_df["positive"] == 1]
    days_since_last_positive = None
    if not positive_rows.empty:
        last_positive_date = positive_rows.iloc[-1]["Date"]
        days_since_last_positive = int((pd.to_datetime(reference_date) - last_positive_date).days)

    has_signal = False
    if days_since_last_positive is not None and days_since_last_positive <= 90:
        has_signal = True
    if rate_90 is not None and rate_90 >= 0.15:
        has_signal = True
    if rate_365 is not None and rate_365 >= 0.10:
        has_signal = True

    return {
        "has_signal": has_signal,
        "days_since_last_positive": days_since_last_positive,
        "recent_positive_rate_90d": round(rate_90, 3) if rate_90 is not None else None,
        "recent_positive_rate_365d": round(rate_365, 3) if rate_365 is not None else None,
    }

def safe_float(val, decimals=2):
    """Safely convert value to float, handling NaN/None."""
    try:
        f_val = float(val)
        if pd.isna(f_val) or np.isnan(f_val):
            return None
        return round(f_val, decimals)
    except (ValueError, TypeError):
        return None


def _map_gee_to_model_inputs(gee_data: dict) -> dict:
    """Map GEE environmental outputs to the XGBoost model's input columns.

    - SST (°C)        -> thetao
    - Salinity (PSU)  -> so
    - Rainfall_mm     -> precip_mm_day
    - Chlorophyll_a_proxy (log10 ratio) -> CHL (approximate mg/m3 proxy)
    - NDVI            -> NDVI_daily, NDVI_raw
    - Wind_u_ms       -> wind_u_ms
    - Wind_v_ms       -> wind_v_ms
    - Wind_speed_ms   -> wind_speed_ms
    """
    if not gee_data:
        return {}

    mapped = {}

    sst = gee_data.get("SST")
    if sst is not None:
        mapped["thetao"] = float(sst)

    sal = gee_data.get("Salinity")
    if sal is not None:
        mapped["so"] = float(sal)

    rain = gee_data.get("Rainfall_mm")
    if rain is not None:
        mapped["precip_mm_day"] = float(rain)

    chl_proxy = gee_data.get("Chlorophyll_a_proxy")
    if chl_proxy is not None:
        try:
            mapped["CHL"] = abs(float(chl_proxy)) * 10.0
        except (TypeError, ValueError):
            pass

    ndvi = gee_data.get("NDVI")
    if ndvi is not None:
        try:
            ndvi_val = float(ndvi)
            mapped["NDVI_daily"] = ndvi_val
            mapped["NDVI_raw"] = ndvi_val
        except (TypeError, ValueError):
            pass

    wind_speed = gee_data.get("Wind_speed_ms")
    if wind_speed is not None:
        try:
            mapped["wind_speed_ms"] = float(wind_speed)
        except (TypeError, ValueError):
            pass

    wind_u = gee_data.get("Wind_u_ms")
    if wind_u is not None:
        try:
            mapped["wind_u_ms"] = float(wind_u)
        except (TypeError, ValueError):
            pass

    wind_v = gee_data.get("Wind_v_ms")
    if wind_v is not None:
        try:
            mapped["wind_v_ms"] = float(wind_v)
        except (TypeError, ValueError):
            pass

    return mapped

def run_daily_update_with_5day_forecast():
    """Generate today's forecast using the actual ML model and latest available data."""
    print("Starting HARIBON v2.0 daily forecast update (ML-Powered)...")
    
    try:
        manifest = get_thesis_winners_manifest()
        manifest_imputation = manifest.get("imputation", {}).get("primary_method", "hybrid_gap_type_adaptive")
        manifest_forecasting = manifest.get("forecasting", {}).get("primary_model", "xgboost")
    except Exception as manifest_error:
        print(f"[WARN] Could not load thesis manifest, continuing with defaults: {manifest_error}")
        manifest = None
        manifest_imputation = "hybrid_gap_type_adaptive"
        manifest_forecasting = "xgboost"

    try:
        historical_df = load_historical_data()
        model, feature_names = load_ml_components(historical_df, manifest=manifest)
        loc_month_means, loc_means, global_means = _build_feature_imputation_stats(historical_df, feature_names)
    except Exception as e:
        print(f"Failed to load ML components or data: {e}")
        import traceback
        traceback.print_exc()
        return

    locations = historical_df['Location_Name'].unique()
    print(f"Generating forecasts for {len(locations)} locations: {locations}")

    location_features = {}
    try:
        with open(settings.LOCATIONS_FILE_PATH, 'r') as f:
            geojson = json.load(f)
        for feat in geojson.get('features', []):
            name = feat.get('properties', {}).get('Name')
            if isinstance(name, str):
                location_features[name] = feat
        print(f"Loaded {len(location_features)} location features for GEE fetch.")
    except Exception as exc:
        print(f"[WARN] Could not load location features from {settings.LOCATIONS_FILE_PATH}: {exc}")

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    forecasts = []

    for location in locations:
        if not isinstance(location, str):
            continue
        
        latest_row = get_latest_data_for_location(historical_df, location)

        if latest_row is None:
            print(f"Skipping {location}: No data found")
            continue
        input_data = latest_row.to_dict()
        input_data['Date'] = today_str

        gee_feature = location_features.get(location)
        gee_data = None
        cmems_data = None
        env_source = "historical_latest"
        env_source_meta = {}
        
        # Try CMEMS first (includes internal baseline fallback)
        if get_cmems_data_for_location is not None:
            try:
                coords = (gee_feature["geometry"]["coordinates"] if gee_feature else None)
                if coords:
                    cmems_data = get_cmems_data_for_location(location, coords, today_str)
            except Exception as exc:
                print(f"[WARN] CMEMS fetch failed for {location}")
        
        # Try GEE as supplement
        if gee_feature is not None and get_environmental_data_for_feature is not None:
            try:
                gee_data = get_environmental_data_for_feature(gee_feature, today_str)
            except Exception as exc:
                print(f"[WARN] GEE fetch failed for {location}")

        # Merge data sources: CMEMS (marine) + GEE (atmospheric/land)
        # First map GEE atmospheric data
        mapped_gee = _map_gee_to_model_inputs(gee_data or {})
        
        # Then merge CMEMS marine data (priority if both available)
        cmems_env = {}
        gee_env = {}
        if cmems_data:
            cmems_env = {k: v for k, v in cmems_data.items() if not k.startswith("_")}
            print(
                f"Using {'live CMEMS' if cmems_data.get('_source') == 'cmems_live' else 'Copernicus baseline'} "
                f"for {location} (marine data): {cmems_env}"
            )
        
        if mapped_gee:
            gee_env = mapped_gee
            print(f"Using live GEE data for {location} (atmospheric/land): {gee_env}")
        
        # Merge both: CMEMS (marine) gets priority, GEE supplements atmospheric/land
        mapped_env = {**gee_env, **cmems_env}  # CMEMS overrides GEE for overlapping keys
        input_data.update(mapped_env)
        
        # Track data sources
        if cmems_data and mapped_gee:
            env_source = "cmems_gee_merged"
            env_source_meta = {
                "cmems_source": cmems_data.get("_source"),
                "cmems_date": cmems_data.get("_source_date"),
                "gee_available": len(mapped_gee) > 0,
                "gee_params": list(mapped_gee.keys()),
            }
            print(f"  => Merged: GEE {len(gee_env)} params + CMEMS {len(cmems_env)} params")
        elif cmems_data:
            env_source = cmems_data.get("_fetch_status", "cmems_live")
            env_source_meta = {
                "cmems_source_date": cmems_data.get("_source_date"),
                "cmems_source_location": cmems_data.get("_source_location"),
                "cmems_fetch_status": cmems_data.get("_fetch_status"),
            }
        elif mapped_gee:
            env_source = "gee_live"
            env_source_meta = {
                "gee_params": list(mapped_gee.keys()),
            }
        else:
            # No live/fallback env source available; feature imputation will handle missing values.
            print(f"No CMEMS/GEE data available for {location}; using thesis imputation fallbacks.")
        
        try:
            print(f"Running forecast inference for {location}...")

            current_month = today.month
            feature_row, observed_non_missing, imputation_sources = _build_feature_row_with_fallbacks(
                feature_names=feature_names,
                source_data=input_data,
                location=location,
                month=current_month,
                reference_date=today,
                historical_df=historical_df,
                loc_month_means=loc_month_means,
                loc_means=loc_means,
                global_means=global_means,
            )

            critical_features = ['CHL', 'thetao', 'so', 'precip_mm_day']
            critical_available = sum(
                1 for key in critical_features if not _is_missing(input_data.get(key, np.nan))
            )
            critical_imputed = sum(
                1
                for key in critical_features
                if _is_missing(input_data.get(key, np.nan)) and not _is_missing(feature_row.get(key, np.nan))
            )
            if env_source == "historical_latest" and critical_imputed > 0:
                env_source = str(manifest_imputation).lower().replace(" ", "_")

            critical_ratio = critical_available / len(critical_features)
            observed_ratio = observed_non_missing / max(len(feature_names), 1)

            X_new = pd.DataFrame([feature_row])
            xgb_prob = float(model.predict_proba(X_new)[:, 1][0])
            probability = xgb_prob
            final_probability_source = "xgboost"

            use_weighted = "ensemble" in str(manifest_forecasting).lower() or "weighted" in str(manifest_forecasting).lower()
            if use_weighted:
                print(f"  [MODEL] Ensemble mode enabled by manifest: {manifest_forecasting}")
                weighted_prob = _predict_weighted_avg_probability(
                    manifest=manifest,
                    historical_df=historical_df,
                    location=location,
                    feature_row=feature_row,
                    xgb_probability=xgb_prob,
                    reference_date=today,
                )
                if weighted_prob is not None:
                    probability = weighted_prob
                    final_probability_source = "weighted_avg_ensemble"
                    print(f"  [MODEL] Using weighted average ensemble probability: {probability:.6f}")
                else:
                    print("  [MODEL] Weighted average ensemble unavailable; falling back to XGBoost probability.")

            historical_signal = _compute_recent_red_tide_signal(
                historical_df=historical_df,
                location=location,
                reference_date=today,
            )

            if probability >= 0.8:
                risk_level = "High Risk"
            elif probability >= 0.5:
                risk_level = "Moderate Risk"
            elif probability >= 0.2:
                risk_level = "Low Risk"
            else:
                risk_level = "Very Low Risk"

            base_confidence = 0.5 + abs(probability - 0.5)

            data_limited = critical_ratio < 0.5 or observed_ratio < 0.7
            if data_limited:
                base_confidence = min(base_confidence, 0.65)
                if risk_level == "Very Low Risk":
                    risk_level = "Low Risk"

            if historical_signal["has_signal"] and risk_level in {"Very Low Risk", "Low Risk"}:
                risk_level = "Moderate Risk"
                base_confidence = min(base_confidence, 0.70)

            confidence = f"{base_confidence * 100:.1f}%"

            if "High" in risk_level:
                explanation = (
                    "Elevated bloom risk driven by current chlorophyll, "
                    "temperature, salinity, and wind conditions."
                )
            elif "Moderate" in risk_level:
                explanation = (
                    "Moderate bloom risk based on a combination of "
                    "environmental factors; continue close monitoring."
                )
            elif "Low" in risk_level:
                explanation = (
                    "Low bloom risk under current environmental "
                    "conditions, but routine monitoring is still advised."
                )
            else:
                explanation = (
                    "Very low bloom risk; environmental conditions are "
                    "currently unfavorable for red tide development."
                )

            if data_limited:
                explanation = (
                    "Forecast generated with limited real-time environmental "
                    "coverage; interpret risk conservatively and verify with "
                    "local monitoring and BFAR advisories."
                )
            elif historical_signal["has_signal"]:
                explanation = (
                    "Moderate bloom risk retained due to persistent recent "
                    "positive red tide history in this location."
                )
            
            recommendations = []
            if "High" in risk_level:
                recommendations = [
                    "HARMFUL ALGAL BLOOM DETECTED",
                    "Do not harvest, buy, or eat shellfish from this area.",
                    "Wait for official BFAR advisory before resuming activities."
                ]
            elif "Moderate" in risk_level:
                recommendations = [
                    "Elevated risk detected.",
                    "Limit harvesting and monitor water color changes.",
                    "Check for latest local advisories."
                ]
            else:
                recommendations = [
                    "Conditions are favorable.",
                    "Shellfish harvesting is permitted.",
                    "Continue regular monitoring."
                ]

            if data_limited:
                recommendations = recommendations + [
                    "Data quality note: key environmental inputs were partially imputed.",
                    "Use this forecast as preliminary guidance and prioritize official advisories with on-site validation."
                ]
            
            coords_map = {
                "Gigantes Islands": {"lat": 11.5975, "lng": 123.3364},
                "Batan Bay": {"lat": 11.5790, "lng": 122.4930},
                "Sapian Bay": {"lat": 11.4936, "lng": 122.6186},
                "Roxas City": {"lat": 11.5853, "lng": 122.7511},
                "Dumanquillas Bay": {"lat": 7.697, "lng": 123.018},
                "Matarinao Bay": {"lat": 11.23, "lng": 125.55},
                "Pilar": {"lat": 11.504, "lng": 122.941},
                "President Roxas": {"lat": 11.496, "lng": 122.914},
            }
            
            curr_coords = coords_map.get(location, {"lat": 11.5, "lng": 122.5})

            display_chl = _select_display_value('CHL', mapped_env, input_data, feature_row, latest_row)
            display_thetao = _select_display_value('thetao', mapped_env, input_data, feature_row, latest_row)
            display_so = _select_display_value('so', mapped_env, input_data, feature_row, latest_row)
            display_rain = _select_display_value('precip_mm_day', mapped_env, input_data, feature_row, latest_row)
            display_wind_speed = _select_display_value('wind_speed_ms', mapped_env, input_data, feature_row, latest_row)
            display_mld = _select_display_value('mlotst', mapped_env, input_data, feature_row, latest_row)
            display_ndvi = _select_display_value('NDVI_daily', mapped_env, input_data, feature_row, latest_row)
            display_ndvi_raw = _select_display_value('NDVI_raw', mapped_env, input_data, feature_row, latest_row)
            display_wind_u = _select_display_value('wind_u_ms', mapped_env, input_data, feature_row, latest_row)
            display_wind_v = _select_display_value('wind_v_ms', mapped_env, input_data, feature_row, latest_row)
            display_uo = _select_display_value('uo', mapped_env, input_data, feature_row, latest_row)
            display_vo = _select_display_value('vo', mapped_env, input_data, feature_row, latest_row)

            forecast = {
                "location": location,
                "latitude": float(curr_coords["lat"]),
                "longitude": float(curr_coords["lng"]),
                "date": today_str,
                "risk_level": risk_level,
                "confidence": confidence,
                "red_tide_probability": risk_level.split(" ")[0], # "High", "Moderate"
                "recommendations": recommendations,
                "contributing_factors": {
                    "chl-a": safe_float(display_chl, 3),
                    "sst": safe_float(display_thetao, 2),
                    "salinity": safe_float(display_so, 2),
                    "rainfall": safe_float(display_rain, 1),
                },
                "environmental_data": {
                    "Chlorophyll-a": f"{safe_float(display_chl, 2)} mg/m3" if safe_float(display_chl, 2) is not None else "N/A",
                    "Temperature": f"{safe_float(display_thetao, 2)} °C" if safe_float(display_thetao, 2) is not None else "N/A",
                    "Salinity (PSU)": f"{safe_float(display_so, 2)} PSU" if safe_float(display_so, 2) is not None else "N/A",
                    "MLD (m)": f"{safe_float(display_mld, 2)} m" if safe_float(display_mld, 2) is not None else "N/A",
                    "Precipitation": f"{safe_float(display_rain, 2)} mm" if safe_float(display_rain, 2) is not None else "N/A",
                    "NDVI": f"{safe_float(display_ndvi, 4)}" if safe_float(display_ndvi, 4) is not None else "N/A",
                    "U-Wind Speed (m/s)": f"{safe_float(display_wind_u, 2)} m/s" if safe_float(display_wind_u, 2) is not None else "N/A",
                    "V-Wind Speed (m/s)": f"{safe_float(display_wind_v, 2)} m/s" if safe_float(display_wind_v, 2) is not None else "N/A",
                    "U-VEL (m/s)": f"{safe_float(display_uo, 3)} m/s" if safe_float(display_uo, 3) is not None else "N/A",
                    "V-VEL (m/s)": f"{safe_float(display_vo, 3)} m/s" if safe_float(display_vo, 3) is not None else "N/A",
                },
                "data_quality": {
                    "quality_score": round(observed_ratio, 2),
                    "confidence_level": "Low" if data_limited else "High",
                    "critical_features_available": critical_available,
                    "critical_features_total": len(critical_features),
                    "coverage_note": "limited" if data_limited else "sufficient",
                    "environment_data_source": env_source,
                    "environment_imputation_strategy": manifest_imputation,
                    "forecasting_model": manifest_forecasting,
                    "base_xgboost_probability": round(xgb_prob, 6),
                    "final_probability_source": final_probability_source,
                    "environment_imputation_sources": {
                        "CHL": imputation_sources.get("CHL"),
                        "thetao": imputation_sources.get("thetao"),
                        "so": imputation_sources.get("so"),
                        "precip_mm_day": imputation_sources.get("precip_mm_day"),
                        "mlotst": imputation_sources.get("mlotst"),
                        "NDVI_daily": imputation_sources.get("NDVI_daily"),
                        "wind_speed_ms": imputation_sources.get("wind_speed_ms"),
                        "wind_u_ms": imputation_sources.get("wind_u_ms"),
                        "wind_v_ms": imputation_sources.get("wind_v_ms"),
                        "uo": imputation_sources.get("uo"),
                        "vo": imputation_sources.get("vo"),
                    },
                    "historical_positive_signal": historical_signal["has_signal"],
                    "days_since_last_positive": historical_signal["days_since_last_positive"],
                    "recent_positive_rate_90d": historical_signal["recent_positive_rate_90d"],
                    "recent_positive_rate_365d": historical_signal["recent_positive_rate_365d"],
                    **env_source_meta,
                },
                "explanation": explanation
            }

            five_day = []
            decay_factor = 0.9
            horizon_conf_decay = 0.95

            # 7-day horizon total: today + next 6 days.
            for i in range(1, 7):
                future_date = today + timedelta(days=i)

                future_prob = probability * (decay_factor ** i)

                future_risk_label = "Low Risk"
                if future_prob > 0.7:
                    future_risk_label = "High Risk"
                elif future_prob > 0.4:
                    future_risk_label = "Moderate Risk"

                future_conf_score = base_confidence * (horizon_conf_decay ** i)
                if base_confidence > 0.7:
                    future_conf_score = max(0.5, future_conf_score)
                else:
                    future_conf_score = max(0.0, future_conf_score)

                day_forecast = {
                    "forecast_day": i,
                    "date": future_date.strftime('%Y-%m-%d'),
                    "day_label": future_date.strftime('%a'),
                    "risk_level": future_risk_label,
                    "confidence": f"{future_conf_score * 100:.1f}%",
                    "probability": future_risk_label.split(" ")[0]
                }
                five_day.append(day_forecast)
                
            forecast["five_day_forecast"] = five_day
            forecasts.append(forecast)

            # Log prediction to database (only if not already logged for this location today)
            if SessionLocal is not None and Location is not None and PredictionLog is not None:
                try:
                    session = SessionLocal()
                    # Get location_id
                    location_obj = session.query(Location).filter_by(location_name=location).first()
                    if location_obj:
                        # Check if prediction for this location and date already exists
                        today_date = today.date()
                        existing_prediction = session.query(PredictionLog).filter(
                            PredictionLog.location_id == location_obj.location_id,
                            PredictionLog.prediction_timestamp.cast(Date) == today_date
                        ).first()

                        if existing_prediction:
                            print(f"Prediction for {location} on {today_str} already exists, skipping log")
                        else:
                            # Extract confidence as float
                            confidence_float = float(confidence.rstrip('%')) / 100.0 if confidence.endswith('%') else float(confidence)

                            prediction_log = PredictionLog(
                                location_id=location_obj.location_id,
                                prediction_timestamp=today,  # Use forecast date instead of current time
                                # 10 Environmental Parameters
                                chlorophyll_a=safe_float(display_chl),
                                ndvi_daily=safe_float(display_ndvi),
                                ndvi_raw=safe_float(display_ndvi_raw),
                                mixed_layer_depth=safe_float(display_mld),
                                precipitation_mm=safe_float(display_rain),
                                salinity=safe_float(display_so),
                                sst=safe_float(display_thetao),
                                eastward_current_velocity=safe_float(display_uo),
                                northward_current_velocity=safe_float(display_vo),
                                wind_speed_ms=safe_float(display_wind_speed),
                                wind_u_component=safe_float(display_wind_u),
                                wind_v_component=safe_float(display_wind_v),
                                # Prediction output
                                risk_level=risk_level,
                                confidence_score=confidence_float
                            )
                            session.add(prediction_log)
                            session.commit()
                            print(f"Logged prediction for {location} to database")
                    session.close()
                except Exception as exc:
                    print(f"[WARN] Failed to log prediction for {location}: {exc}")

            print(f"Generated forecast for {location}: {risk_level}")

        except Exception as e:
            print(f"Error generating forecast for {location}: {e}")
            import traceback
            traceback.print_exc()

    output_data = {
        "last_updated": datetime.now().isoformat(),
        "system_version": f"v2.0 ({manifest_forecasting})",
        "manifest": {
            "path": str(settings.THESIS_WINNERS_PATH),
            "imputation_primary": manifest_imputation,
            "forecasting_primary": manifest_forecasting,
        },
        "forecasts": forecasts
    }

    processed_dir = settings.PROCESSED_DATA_DIR
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_dir / f"daily_forecast_{today_str}.json"

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Forecast saved to: {output_file}")

    if SessionLocal is not None and DailyForecast is not None:
        try:
            session = SessionLocal()
            db_obj = DailyForecast(
                forecast_date=today.date(),
                system_version=output_data["system_version"],
                payload=output_data,
            )
            session.add(db_obj)
            session.commit()
            session.close()
            print("Daily forecast also stored in PostgreSQL (daily_forecasts table).")
        except Exception as exc:
            print(f"[WARN] Failed to store daily forecast in PostgreSQL: {exc}")


if __name__ == "__main__":
    run_daily_update_with_5day_forecast()
