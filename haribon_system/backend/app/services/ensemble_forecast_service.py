from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_DIR.parent.parent
_ENSEMBLE_CODE_DIR = _PROJECT_ROOT / "ensemble_model" / "code"
_ENSEMBLE_SAVED_MODEL_DIR = _PROJECT_ROOT / "ensemble_model" / "saved_model"
_DATASET_PATH = _PROJECT_ROOT / "final_compiled_dataset" / "Combined_Labeled.csv"

if str(_ENSEMBLE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENSEMBLE_CODE_DIR))

from ensemble_data import (  # type: ignore  # noqa: E402
    DEFAULT_DATASET_PATH,
    FEATURES,
    LOOKBACK,
    _impute_df,
    build_splits,
    load_and_prepare,
)
from ensemble_inference import predict_all  # type: ignore  # noqa: E402


BASE_MODEL_ORDER = ("lstm", "gru", "transformer", "xgboost")
DEFAULT_TRANSFORMER_SCENARIO = "hybrid_adaptive"


@dataclass
class LiveSplitData:
    X_seq_train: np.ndarray
    X_seq_test: np.ndarray
    X_tab_train: np.ndarray
    X_tab_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    split_num: int = 0


def _clean_probability(value: Any) -> float:
    try:
        cleaned = float(value)
    except Exception:
        return 0.5
    if np.isnan(cleaned):
        return 0.5
    return float(np.clip(cleaned, 0.0, 1.0))


def _probability_to_risk_level(probability: float) -> str:
    if probability < 0.20:
        return "Very Low Risk"
    if probability < 0.40:
        return "Low Risk"
    if probability < 0.70:
        return "Moderate Risk"
    return "High Risk"


def _confidence_from_probability(probability: float) -> str:
    confidence = 0.5 + abs(probability - 0.5)
    return f"{confidence * 100:.1f}%"


def _build_explanation(risk_level: str, probability: float, base_probs: dict[str, float]) -> str:
    ordered = sorted(base_probs.items(), key=lambda item: item[1], reverse=True)
    model_summary = ", ".join(f"{name}={score:.3f}" for name, score in ordered)

    if "High" in risk_level:
        prefix = "Elevated bloom risk detected by the ensemble"
    elif "Moderate" in risk_level:
        prefix = "Moderate bloom risk detected by the ensemble"
    elif "Low" in risk_level:
        prefix = "Low bloom risk detected by the ensemble"
    else:
        prefix = "Very low bloom risk detected by the ensemble"

    return f"{prefix} (meta probability={probability:.3f}; base outputs: {model_summary})."


def _build_windows(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    feature_cols = [col for col in FEATURES if col in frame.columns]
    if len(feature_cols) != len(FEATURES):
        missing = [col for col in FEATURES if col not in frame.columns]
        raise ValueError(f"Missing ensemble features: {missing}")

    if "red_tide_label" not in frame.columns:
        frame = frame.copy()
        frame["red_tide_label"] = 0

    frame = frame.sort_values("Date").reset_index(drop=True)
    values = frame[feature_cols].to_numpy(dtype=np.float32)
    labels = pd.to_numeric(frame["red_tide_label"], errors="coerce").fillna(0).astype(int).to_numpy()
    dates = pd.to_datetime(frame["Date"], errors="coerce").to_numpy()

    windows = []
    window_labels = []
    window_dates = []
    for index in range(LOOKBACK - 1, len(frame)):
        window = values[index - LOOKBACK + 1 : index + 1]
        if window.shape[0] != LOOKBACK:
            continue
        windows.append(window)
        window_labels.append(labels[index])
        window_dates.append(dates[index])

    if not windows:
        raise ValueError("Not enough history to build any ensemble windows")

    return np.stack(windows, axis=0), np.asarray(window_labels), np.asarray(window_dates)


def _prepare_location_frame(
    historical_df: pd.DataFrame,
    location_name: str,
    new_data_point: dict[str, Any] | None = None,
) -> pd.DataFrame:
    history = historical_df[historical_df["Location_Name"] == location_name].copy()
    if history.empty:
        raise ValueError(f"No historical data found for location '{location_name}'")

    history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
    history = history.dropna(subset=["Date"])

    combined = history
    if new_data_point is not None:
        current_row = pd.DataFrame([new_data_point.copy()])
        current_row["Date"] = pd.to_datetime(current_row["Date"], errors="coerce")
        current_row["red_tide_label"] = current_row.get("red_tide_label", 0)
        combined = pd.concat([combined, current_row], ignore_index=True)

    combined = combined.dropna(subset=["Date"]).sort_values("Date")
    combined = combined.drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)

    for column in FEATURES:
        if column not in combined.columns:
            combined[column] = np.nan
    if "red_tide_label" not in combined.columns:
        combined["red_tide_label"] = 0

    combined["Month"] = combined["Date"].dt.month
    combined["Day"] = combined["Date"].dt.day

    combined = _impute_df(combined, [col for col in FEATURES if col in combined.columns], method="hybrid_adaptive")
    combined["red_tide_label"] = pd.to_numeric(combined["red_tide_label"], errors="coerce").fillna(0).astype(int)
    return combined


def _build_live_split(historical_df: pd.DataFrame, new_data_point: dict[str, Any]) -> tuple[LiveSplitData, pd.Series]:
    target_location = new_data_point.get("Location_Name")
    if not target_location:
        raise ValueError("new_data_point must include Location_Name")

    train_seq_parts: list[np.ndarray] = []
    train_tab_parts: list[np.ndarray] = []
    train_y_parts: list[np.ndarray] = []
    target_test_split: np.ndarray | None = None
    latest_row: pd.Series | None = None

    locations = [loc for loc in historical_df["Location_Name"].dropna().unique().tolist() if isinstance(loc, str)]
    for location_name in locations:
        loc_df = _prepare_location_frame(
            historical_df=historical_df,
            location_name=location_name,
            new_data_point=new_data_point if location_name == target_location else None,
        )
        windows, labels, _ = _build_windows(loc_df)
        tabular = windows[:, -1, :]

        if location_name == target_location:
            if windows.shape[0] < 2:
                raise ValueError("Not enough rolling windows to evaluate the live ensemble")
            target_test_split = windows[-1:]
            latest_row = loc_df.iloc[-1]
            train_seq_parts.append(windows[:-1])
            train_tab_parts.append(tabular[:-1])
            train_y_parts.append(labels[:-1])
        else:
            train_seq_parts.append(windows)
            train_tab_parts.append(tabular)
            train_y_parts.append(labels)

    if target_test_split is None or latest_row is None:
        raise ValueError("Unable to construct live ensemble inputs")

    X_seq_train = np.concatenate(train_seq_parts, axis=0)
    X_tab_train = np.concatenate(train_tab_parts, axis=0)
    y_train = np.concatenate(train_y_parts, axis=0)

    live_split = LiveSplitData(
        X_seq_train=X_seq_train,
        X_seq_test=target_test_split,
        X_tab_train=X_tab_train,
        X_tab_test=target_test_split[:, -1, :],
        y_train=y_train,
        y_test=np.array([int(pd.to_numeric(latest_row.get("red_tide_label", 0), errors="coerce") or 0)]),
        split_num=6,
    )

    return live_split, latest_row


def predict_ensemble_risk(
    new_data_point: dict[str, Any],
    historical_df: pd.DataFrame,
    transformer_scenario: str = DEFAULT_TRANSFORMER_SCENARIO,
) -> dict[str, Any]:
    """Predict red tide risk using weighted average ensemble."""
    live_split, latest_row = _build_live_split(historical_df, new_data_point)

    probs = predict_all(
        live_split,
        transformer_saved_dir=_ENSEMBLE_SAVED_MODEL_DIR,
        transformer_scenario=transformer_scenario,
    )

    base_probs = {
        model_name: _clean_probability(probs.get(model_name, np.array([0.5]))[0])
        for model_name in BASE_MODEL_ORDER
    }

    # Weighted average ensemble using AUC weights from ensemble evaluation
    weights = {
        "lstm": 0.736298,
        "gru": 0.699018,
        "transformer": 0.626543,
        "xgboost": 0.70822
    }

    weighted_sum = sum(weights[name] * base_probs[name] for name in BASE_MODEL_ORDER)
    total_weight = sum(weights[name] for name in BASE_MODEL_ORDER)
    meta_probability = weighted_sum / total_weight

    risk_level = _probability_to_risk_level(meta_probability)
    confidence = _confidence_from_probability(meta_probability)
    explanation = _build_explanation(risk_level, meta_probability, base_probs)

    return {
        "risk_level": risk_level,
        "probability": meta_probability,
        "confidence": confidence,
        "explanation": explanation,
        "base_model_probabilities": base_probs,
        "latest_inputs": {
            key: latest_row.get(key)
            for key in (
                "CHL",
                "NDVI_daily",
                "mlotst",
                "precip_mm_day",
                "so",
                "thetao",
                "uo",
                "vo",
                "wind_speed_ms",
                "wind_u_ms",
                "wind_v_ms",
            )
            if key in latest_row
        },
    }
