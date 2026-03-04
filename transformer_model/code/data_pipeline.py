"""
Transformer data pipeline using the final thesis dataset (Combined_Labeled.csv).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


_THIS_DIR = Path(__file__).resolve().parent
_TRANSFORMER_DIR = _THIS_DIR.parent
_ROOT = _TRANSFORMER_DIR.parent

DEFAULT_DATASET_PATH = _ROOT / "final_compiled_dataset" / "Combined_Labeled.csv"

NON_FEATURE_COLS = {"Location_Name", "Date", "red_tide", "red_tide_label", "target_label"}


@dataclass
class RollingSplit:
    split_num: int
    cutoff_date: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def load_final_dataset(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load and standardize Combined_Labeled.csv."""
    df = pd.read_csv(dataset_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Location_Name", "Date"]).reset_index(drop=True)
    return df


def _to_binary_label(series: pd.Series, threshold: float = 0.5) -> pd.Series:
    """Convert red_tide_label to binary class with configurable threshold."""
    numeric = pd.to_numeric(series, errors="coerce")
    return (numeric >= threshold).astype(float)


def _feature_columns(df: pd.DataFrame) -> List[str]:
    cols: List[str] = []
    for c in df.columns:
        if c in NON_FEATURE_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def _hybrid_gap_adaptive_impute_location(
    loc_df: pd.DataFrame,
    feature_cols: List[str],
    max_linear_gap: int = 14,
) -> pd.DataFrame:
    """
    Lightweight hybrid-adaptive imputation.

    Strategy per feature per location:
    1) linear interpolation for short gaps (<= max_linear_gap)
    2) monthly climatology for remaining long/systematic gaps
    3) location median fallback
    """
    loc_df = loc_df.copy()

    for col in feature_cols:
        series = pd.to_numeric(loc_df[col], errors="coerce")

        short_filled = series.interpolate(
            method="linear",
            limit=max_linear_gap,
            limit_direction="both",
        )

        month = loc_df["Date"].dt.month
        month_clim = short_filled.groupby(month).transform("mean")
        long_filled = short_filled.fillna(month_clim)

        fallback = float(np.nanmedian(series.to_numpy(dtype=float)))
        if np.isnan(fallback):
            fallback = 0.0

        loc_df[col] = long_filled.fillna(fallback)

    return loc_df


def prepare_scenario_dataframe(
    base_df: pd.DataFrame,
    scenario: str,
    label_threshold: float = 0.5,
    max_linear_gap: int = 14,
) -> pd.DataFrame:
    """
    Prepare model-ready frame for one scenario.

    Scenarios:
    - hybrid_adaptive: perform adaptive imputation before modeling
    - native_masking : no imputation; preserve raw gaps + missingness indicators
    """
    if scenario not in {"hybrid_adaptive", "native_masking"}:
        raise ValueError(f"Unsupported scenario: {scenario}")

    df = base_df.copy()
    feat_cols = _feature_columns(df)

    for col in feat_cols:
        df[f"is_missing_{col}"] = pd.to_numeric(df[col], errors="coerce").isna().astype(int)

    if scenario == "hybrid_adaptive":
        chunks: List[pd.DataFrame] = []
        for _, loc_df in df.groupby("Location_Name", sort=False):
            chunks.append(
                _hybrid_gap_adaptive_impute_location(
                    loc_df,
                    feat_cols,
                    max_linear_gap=max_linear_gap,
                )
            )
        df = pd.concat(chunks, axis=0).sort_values(["Location_Name", "Date"]).reset_index(drop=True)

    location_ohe = pd.get_dummies(df["Location_Name"], prefix="loc", dtype=float)
    df = pd.concat([df, location_ohe], axis=1)

    df["target_label"] = _to_binary_label(df["red_tide_label"], threshold=label_threshold)

    # keep only rows where label exists in source data
    df = df[pd.to_numeric(df["red_tide_label"], errors="coerce").notna()].copy()
    df = df.sort_values(["Location_Name", "Date"]).reset_index(drop=True)
    return df


def generate_rolling_origin_splits(
    labeled_df: pd.DataFrame,
    num_splits: int = 4,
    test_window_days: int = 90,
    min_train_days: int = 365,
) -> List[RollingSplit]:
    """Generate rolling-origin splits from available labeled dates."""
    unique_dates = np.array(sorted(labeled_df["Date"].dropna().unique()))

    if len(unique_dates) < (min_train_days + test_window_days + 1):
        raise ValueError(
            "Not enough dated rows for requested split config: "
            f"need at least {min_train_days + test_window_days + 1} unique dates, "
            f"found {len(unique_dates)}"
        )

    start_idx = min_train_days - 1
    end_idx = len(unique_dates) - test_window_days - 1
    if end_idx <= start_idx:
        raise ValueError("Invalid split parameters; reduce test_window_days or min_train_days.")

    cutoff_idxs = np.linspace(start_idx, end_idx, num_splits, dtype=int)

    splits: List[RollingSplit] = []
    for i, cutoff_idx in enumerate(cutoff_idxs, start=1):
        cutoff_date = pd.Timestamp(unique_dates[cutoff_idx])
        test_start = pd.Timestamp(unique_dates[cutoff_idx + 1])
        test_end_idx = min(cutoff_idx + test_window_days, len(unique_dates) - 1)
        test_end = pd.Timestamp(unique_dates[test_end_idx])

        splits.append(
            RollingSplit(
                split_num=i,
                cutoff_date=cutoff_date,
                test_start=test_start,
                test_end=test_end,
            )
        )

    return splits


def make_sequence_dataset_for_split(
    scenario_df: pd.DataFrame,
    split: RollingSplit,
    history_days: int = 30,
) -> Dict[str, np.ndarray]:
    """Build Transformer sequences per location for one rolling split."""
    df = scenario_df.copy()

    feature_cols = [
        c for c in df.columns
        if c not in NON_FEATURE_COLS
        and c != "target_label"
        and pd.api.types.is_numeric_dtype(df[c])
    ]

    all_train_seq: List[np.ndarray] = []
    all_train_y: List[np.ndarray] = []
    all_test_seq: List[np.ndarray] = []
    all_test_y: List[np.ndarray] = []

    for _, loc_df in df.groupby("Location_Name", sort=False):
        loc_df = loc_df.sort_values("Date").reset_index(drop=True)

        X = loc_df[feature_cols].to_numpy(dtype=np.float32)
        y = loc_df["target_label"].to_numpy(dtype=np.int64)
        d = loc_df["Date"].to_numpy(dtype="datetime64[ns]")

        train_mask = d <= np.datetime64(split.cutoff_date)
        test_mask = (d >= np.datetime64(split.test_start)) & (d <= np.datetime64(split.test_end))

        idxs = np.arange(len(loc_df))
        for idx in idxs:
            start = idx - history_days + 1
            if start < 0:
                continue

            seq = X[start : idx + 1]
            if seq.shape[0] != history_days:
                continue

            if train_mask[idx]:
                all_train_seq.append(seq)
                all_train_y.append(np.array([y[idx]], dtype=np.int64))
            elif test_mask[idx]:
                all_test_seq.append(seq)
                all_test_y.append(np.array([y[idx]], dtype=np.int64))

    if all_train_seq:
        X_train = np.stack(all_train_seq).astype(np.float32)
        y_train = np.concatenate(all_train_y).astype(np.int64)
    else:
        X_train = np.empty((0, history_days, len(feature_cols)), dtype=np.float32)
        y_train = np.empty((0,), dtype=np.int64)

    if all_test_seq:
        X_test = np.stack(all_test_seq).astype(np.float32)
        y_test = np.concatenate(all_test_y).astype(np.int64)
    else:
        X_test = np.empty((0, history_days, len(feature_cols)), dtype=np.float32)
        y_test = np.empty((0,), dtype=np.int64)

    if X_train.shape[0] > 0:
        mean = np.nanmean(X_train, axis=(0, 1), keepdims=True)
        std = np.nanstd(X_train, axis=(0, 1), keepdims=True)
        std = np.where(std < 1e-8, 1.0, std)

        X_train = (X_train - mean) / std
        X_test = (X_test - mean) / std

        X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
        X_test = np.nan_to_num(X_test, nan=0.0, posinf=0.0, neginf=0.0)

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": y_test,
        "feature_names": np.array(feature_cols),
    }
