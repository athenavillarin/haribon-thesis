"""
ensemble_data.py
================
Shared data loading, imputation, and split generation for the ensemble pipeline.

Defines the 6 common rolling-origin splits aligned to LSTM/GRU yearly splits:
  Split 1: train ≤ 2019-12-31 | test = full year 2020
  Split 2: train ≤ 2020-12-31 | test = full year 2021
  Split 3: train ≤ 2021-12-31 | test = full year 2022
  Split 4: train ≤ 2022-12-31 | test = full year 2023
    Split 5: train ≤ 2023-12-31 | test = full year 2024
    Split 6: train ≤ 2024-12-31 | test = years 2025-2026

Produces both:
  - Sequence format (lookback=30 days) for LSTM / GRU / Transformer
  - Tabular format for XGBoost
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent.parent
DEFAULT_DATASET_PATH = _ROOT / "final_compiled_dataset" / "Combined_Labeled.csv"

# ---------------------------------------------------------------------------
# Feature & target config — matches LSTM / GRU / Transformer training setup
# ---------------------------------------------------------------------------
FEATURES = [
    "CHL", "NDVI_daily", "mlotst", "precip_mm_day",
    "so", "thetao", "uo", "vo",
    "wind_speed_ms", "wind_u_ms", "wind_v_ms",
]
TARGET = "red_tide_label"
LOOKBACK = 30  # sliding-window length in days

IMPUTATION_METHODS = [
    "linear_time",
    "polynomial2_time",
    "climatological_month_day",
    "hybrid_adaptive",
]

# ---------------------------------------------------------------------------
# Split definitions
# ---------------------------------------------------------------------------
SPLITS = [
    {"split_num": 1, "train_end": "2019-12-31", "test_start": "2020-01-01", "test_end": "2020-12-31"},
    {"split_num": 2, "train_end": "2020-12-31", "test_start": "2021-01-01", "test_end": "2021-12-31"},
    {"split_num": 3, "train_end": "2021-12-31", "test_start": "2022-01-01", "test_end": "2022-12-31"},
    {"split_num": 4, "train_end": "2022-12-31", "test_start": "2023-01-01", "test_end": "2023-12-31"},
    {"split_num": 5, "train_end": "2023-12-31", "test_start": "2024-01-01", "test_end": "2024-12-31"},
    {"split_num": 6, "train_end": "2024-12-31", "test_start": "2025-01-01", "test_end": "2026-12-31"},
]


@dataclass
class SplitData:
    split_num: int
    train_end: str
    test_start: str
    test_end: str
    # Sequence format (LSTM / GRU / Transformer)
    X_seq_train: np.ndarray   # shape: (N_train, LOOKBACK, n_features)
    X_seq_test:  np.ndarray   # shape: (N_test,  LOOKBACK, n_features)
    # Tabular format (XGBoost) — last row of each window
    X_tab_train: np.ndarray   # shape: (N_train, n_features)
    X_tab_test:  np.ndarray   # shape: (N_test,  n_features)
    y_train: np.ndarray       # binary labels, shape: (N_train,)
    y_test:  np.ndarray       # binary labels, shape: (N_test,)
    dates_test: np.ndarray    # test dates aligned to y_test


# ---------------------------------------------------------------------------
# Imputation — Hybrid Gap-Adaptive (matches xgboost_model, lstm, gru)
# ---------------------------------------------------------------------------

def _impute_df(df: pd.DataFrame, feature_cols: List[str], method: str = "hybrid_adaptive") -> pd.DataFrame:
    """Apply selected imputation method per location for ensemble input features."""
    df = df.copy()

    if method not in IMPUTATION_METHODS:
        raise ValueError(f"Unsupported imputation method: {method}")

    if method == "linear_time":
        for loc in df["Location_Name"].unique():
            mask = df["Location_Name"] == loc
            df.loc[mask, feature_cols] = (
                df.loc[mask, feature_cols]
                .interpolate(method="linear", limit_direction="both")
            )

    elif method == "polynomial2_time":
        for loc in df["Location_Name"].unique():
            mask = df["Location_Name"] == loc
            try:
                df.loc[mask, feature_cols] = (
                    df.loc[mask, feature_cols]
                    .interpolate(method="polynomial", order=2, limit_direction="both")
                )
            except Exception as exc:
                raise RuntimeError(
                    "Polynomial imputation failed. Ensure scipy is installed and data is numeric."
                ) from exc

    elif method == "climatological_month_day":
        for col in feature_cols:
            df[col] = df.groupby(["Location_Name", "Month", "Day"])[col].transform(
                lambda x: x.fillna(x.mean())
            )

    elif method == "hybrid_adaptive":
        for loc in df["Location_Name"].unique():
            mask = df["Location_Name"] == loc
            # Phase 1: linear interpolation ≤14 days
            df.loc[mask, feature_cols] = (
                df.loc[mask, feature_cols]
                .interpolate(method="linear", limit=14, limit_direction="both")
            )
        # Phase 2: climatological mean (Location × Month)
        for col in feature_cols:
            df[col] = df.groupby(["Location_Name", "Month"])[col].transform(
                lambda x: x.fillna(x.mean())
            )
        # Phase 3: location mean
        for col in feature_cols:
            df[col] = df.groupby("Location_Name")[col].transform(
                lambda x: x.fillna(x.mean())
            )

    # Global fallback shared by all methods to avoid downstream NaNs
    if df[feature_cols].isna().any().any():
        # First fallback: location means
        for col in feature_cols:
            df[col] = df.groupby("Location_Name")[col].transform(
                lambda x: x.fillna(x.mean())
            )
    if df[feature_cols].isna().any().any():
        # Final fallback: global means
        df[feature_cols] = df[feature_cols].fillna(df[feature_cols].mean())

    return df


# ---------------------------------------------------------------------------
# Sequence builder
# ---------------------------------------------------------------------------

def _build_sequences(
    loc_df: pd.DataFrame,
    feature_cols: List[str],
    lookback: int,
    date_mask: pd.Series,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build sliding window sequences for one location subset."""
    loc_df = loc_df.reset_index(drop=True)
    X_arr = loc_df[feature_cols].to_numpy(dtype=np.float32)
    y_arr = loc_df["red_tide_binary"].to_numpy(dtype=np.int64)
    d_arr = loc_df["Date"].to_numpy(dtype="datetime64[ns]")
    in_mask = date_mask.reindex(loc_df.index, fill_value=False).to_numpy()

    seqs, labels, dates, tabs = [], [], [], []
    for i in range(lookback - 1, len(loc_df)):
        if not in_mask[i]:
            continue
        window = X_arr[i - lookback + 1 : i + 1]
        if window.shape[0] != lookback:
            continue
        seqs.append(window)
        labels.append(y_arr[i])
        dates.append(d_arr[i])
        tabs.append(X_arr[i])  # last timestep of window → tabular row

    if seqs:
        return (
            np.stack(seqs, axis=0),
            np.array(labels, dtype=np.int64),
            np.array(dates),
            np.stack(tabs, axis=0),
        )
    empty_seq = np.empty((0, lookback, len(feature_cols)), dtype=np.float32)
    empty_tab = np.empty((0, len(feature_cols)), dtype=np.float32)
    return empty_seq, np.empty((0,), dtype=np.int64), np.empty((0,)), empty_tab


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_and_prepare(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    imputation_method: str = "hybrid_adaptive",
) -> pd.DataFrame:
    """Load dataset, add helper columns, apply selected imputation, return clean df."""
    df = pd.read_csv(dataset_path, parse_dates=["Date"])
    df = df.sort_values(["Location_Name", "Date"]).reset_index(drop=True)

    # Drop rows with missing target
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    df["red_tide_binary"] = (df[TARGET] >= 0.5).astype(int)
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

    # Identify available feature columns (intersection with FEATURES list)
    available = [f for f in FEATURES if f in df.columns]
    df = _impute_df(df, available, method=imputation_method)
    return df


def build_splits(df: pd.DataFrame) -> List[SplitData]:
    """Build SplitData objects for all 6 common rolling-origin splits."""
    feature_cols = [f for f in FEATURES if f in df.columns]
    results: List[SplitData] = []

    for cfg in SPLITS:
        train_end   = pd.Timestamp(cfg["train_end"])
        test_start  = pd.Timestamp(cfg["test_start"])
        test_end    = pd.Timestamp(cfg["test_end"])

        # Only use rows whose labels are available
        sub = df.copy()
        train_mask_global = sub["Date"] <= train_end
        test_mask_global  = (sub["Date"] >= test_start) & (sub["Date"] <= test_end)

        all_seq_train, all_y_train, all_tab_train = [], [], []
        all_seq_test,  all_y_test,  all_tab_test, all_dates_test = [], [], [], []

        for _, loc_df in sub.groupby("Location_Name", sort=False):
            loc_df = loc_df.sort_values("Date").reset_index(drop=True)

            # Train sequences — can use any lookback window in train region
            # We allow the lookback window to reach before train_end
            # Mask: the *target* timestep must be in the train region
            t_mask = loc_df["Date"] <= train_end

            X_s, y_s, _, X_t = _build_sequences(loc_df, feature_cols, LOOKBACK, t_mask)
            if X_s.shape[0] > 0:
                all_seq_train.append(X_s)
                all_y_train.append(y_s)
                all_tab_train.append(X_t)

            # Test sequences — target timestep in test region
            te_mask = (loc_df["Date"] >= test_start) & (loc_df["Date"] <= test_end)
            X_se, y_se, d_se, X_te = _build_sequences(loc_df, feature_cols, LOOKBACK, te_mask)
            if X_se.shape[0] > 0:
                all_seq_test.append(X_se)
                all_y_test.append(y_se)
                all_tab_test.append(X_te)
                all_dates_test.append(d_se)

        def _concat_or_empty(lst, ndim, shape_tail):
            if lst:
                return np.concatenate(lst, axis=0)
            return np.empty((0,) + shape_tail, dtype=np.float32)

        n_feat = len(feature_cols)
        results.append(SplitData(
            split_num   = cfg["split_num"],
            train_end   = cfg["train_end"],
            test_start  = cfg["test_start"],
            test_end    = cfg["test_end"],
            X_seq_train = _concat_or_empty(all_seq_train, 3, (LOOKBACK, n_feat)),
            X_seq_test  = _concat_or_empty(all_seq_test,  3, (LOOKBACK, n_feat)),
            X_tab_train = _concat_or_empty(all_tab_train, 2, (n_feat,)),
            X_tab_test  = _concat_or_empty(all_tab_test,  2, (n_feat,)),
            y_train     = np.concatenate(all_y_train) if all_y_train else np.empty((0,), dtype=np.int64),
            y_test      = np.concatenate(all_y_test)  if all_y_test  else np.empty((0,), dtype=np.int64),
            dates_test  = np.concatenate(all_dates_test) if all_dates_test else np.empty((0,)),
        ))

    return results


def scale_splits(splits: List[SplitData]) -> Tuple[List[SplitData], List[object]]:
    """
    Fit a MinMaxScaler per split on train sequences, apply to test.

    Returns (scaled_splits, scalers) — scalers are provided so inference
    functions can re-use them when loading pre-trained models.
    """
    from sklearn.preprocessing import MinMaxScaler  # imported here to keep top-level imports light

    scaled, scalers = [], []
    for s in splits:
        n_train, Lbk, n_feat = s.X_seq_train.shape if s.X_seq_train.ndim == 3 else (0, LOOKBACK, len(FEATURES))
        if n_train == 0:
            scalers.append(None)
            scaled.append(s)
            continue

        scaler = MinMaxScaler()
        flat_train = s.X_seq_train.reshape(-1, n_feat)
        scaler.fit(flat_train)

        X_seq_train_sc = scaler.transform(s.X_seq_train.reshape(-1, n_feat)).reshape(s.X_seq_train.shape)
        X_seq_test_sc  = scaler.transform(s.X_seq_test.reshape(-1, n_feat)).reshape(s.X_seq_test.shape) \
            if s.X_seq_test.shape[0] > 0 else s.X_seq_test
        X_tab_train_sc = scaler.transform(s.X_tab_train) if s.X_tab_train.shape[0] > 0 else s.X_tab_train
        X_tab_test_sc  = scaler.transform(s.X_tab_test)  if s.X_tab_test.shape[0] > 0  else s.X_tab_test

        # Replace with scaled copies
        import copy
        scaled_split = copy.copy(s)
        scaled_split.X_seq_train = X_seq_train_sc
        scaled_split.X_seq_test  = X_seq_test_sc
        scaled_split.X_tab_train = X_tab_train_sc
        scaled_split.X_tab_test  = X_tab_test_sc

        scaled.append(scaled_split)
        scalers.append(scaler)

    return scaled, scalers
