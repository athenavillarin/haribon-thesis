"""
==============================================================================
Feature Engineering
==============================================================================
Purpose:
    Transform imputed long-format data into a wide feature matrix ready for
    XGBoost training. Applied identically across ALL imputation methods to
    ensure fair downstream comparison.

Feature Groups:
    1. Spatial Differences  — ΔX = X_Gigantes − X_Roxas for all 15 variables
    2. Rolling Statistics   — 7d, 14d, 30d mean & std for CHL, SST, Salinity
    3. Calendar Features    — day-of-year, month, is_habagat boolean
    4. Derived Indices      — CHL anomaly, SST stress indicator
    5. Imputation Flags     — binary was_imputed_<var> from mask.csv

Input:
    imputed_df  : long-format DataFrame after imputation
                  columns: Location_Name, Date, CHL, mlotst, no3, ...
    mask_df     : long-format mask DataFrame (True = was artificially masked)
                  same shape as imputed_df

Output:
    wide-format DataFrame: one row per date
    target column: 'CHL_Gigantes' (Chlorophyll at primary bloom site)

==============================================================================
"""

import numpy as np
import pandas as pd
from typing import Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GIGANTES = "Gigantes Polygon"
ROXAS    = "Roxas Polygon"

VARIABLES: list[str] = [
    "CHL", "mlotst", "no3", "o2", "po4", "so", "thetao", "uo", "vo",
    "NDVI_daily", "NDVI_raw", "precip_mm_day", "wind_speed_ms",
    "wind_u_ms", "wind_v_ms",
]

# Variables for which rolling statistics are computed
ROLLING_VARS: list[str] = ["CHL", "thetao", "so"]

# Rolling window sizes (days)
ROLLING_WINDOWS: list[int] = [7, 14, 30]

# SST threshold for thermal stress (°C)
SST_STRESS_THRESHOLD: float = 29.5

# Habagat monsoon months (June–October inclusive)
HABAGAT_MONTHS: set[int] = {6, 7, 8, 9, 10}


# ---------------------------------------------------------------------------
# Step 1: Pivot long → wide
# ---------------------------------------------------------------------------

def pivot_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert long-format data (one row per location × date) to wide format
    (one row per date, with Gigantes and Roxas columns side by side).

    Args:
        df: Long-format DataFrame with columns
            [Location_Name, Date, CHL, mlotst, ...]

    Returns:
        Wide-format DataFrame indexed by Date.
        Column pattern: <variable>_Gigantes, <variable>_Roxas
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    loc_abbrev = {GIGANTES: "Gigantes", ROXAS: "Roxas"}
    frames = []
    for loc, abbrev in loc_abbrev.items():
        loc_df = (
            df[df["Location_Name"] == loc][["Date"] + VARIABLES]
            .copy()
            .rename(columns={v: f"{v}_{abbrev}" for v in VARIABLES})
            .set_index("Date")
        )
        frames.append(loc_df)

    wide = pd.concat(frames, axis=1).sort_index()
    return wide


# ---------------------------------------------------------------------------
# Step 2: Spatial difference features  ΔX = X_Gig − X_Rox
# ---------------------------------------------------------------------------

def add_spatial_differences(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ΔX = X_Gigantes − X_Roxas for every variable and append as
    new columns named Delta_<variable>.

    Args:
        wide: Wide-format DataFrame from pivot_to_wide().

    Returns:
        wide with additional Delta_* columns.
    """
    wide = wide.copy()
    for var in VARIABLES:
        g_col = f"{var}_Gigantes"
        r_col = f"{var}_Roxas"
        if g_col in wide.columns and r_col in wide.columns:
            wide[f"Delta_{var}"] = wide[g_col] - wide[r_col]
    return wide


# ---------------------------------------------------------------------------
# Step 3: Rolling temporal statistics
# ---------------------------------------------------------------------------

def add_rolling_features(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 7-day, 14-day, and 30-day rolling mean and standard deviation
    for CHL, SST (thetao), and Salinity (so) at both locations.

    Rolling statistics use only past values (min_periods=1, no look-ahead).

    Args:
        wide: Wide-format DataFrame with location columns.

    Returns:
        wide with additional rolling_mean_* and rolling_std_* columns.
    """
    wide = wide.copy()
    for var in ROLLING_VARS:
        for loc in ("Gigantes", "Roxas"):
            col = f"{var}_{loc}"
            if col not in wide.columns:
                continue
            series = wide[col]
            for win in ROLLING_WINDOWS:
                wide[f"{col}_roll{win}mean"] = (
                    series.rolling(win, min_periods=1).mean()
                )
                wide[f"{col}_roll{win}std"] = (
                    series.rolling(win, min_periods=1).std().fillna(0.0)
                )
    return wide


# ---------------------------------------------------------------------------
# Step 4: Calendar features
# ---------------------------------------------------------------------------

def add_calendar_features(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Append time-based calendar features derived from the DatetimeIndex.

    Columns added:
        day_of_year  — integer 1-366
        month        — integer 1-12
        is_habagat   — 1 if month is in {6,7,8,9,10}, else 0

    Args:
        wide: Wide-format DataFrame with DatetimeIndex.

    Returns:
        wide with calendar columns appended.
    """
    wide = wide.copy()
    wide["day_of_year"] = wide.index.dayofyear
    wide["month"]       = wide.index.month
    wide["is_habagat"]  = wide["month"].isin(HABAGAT_MONTHS).astype(int)
    return wide


# ---------------------------------------------------------------------------
# Step 5: Derived domain indices
# ---------------------------------------------------------------------------

def add_derived_indices(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Compute domain-specific derived features recommended by the HARIBON
    spatial analysis (Task 3).

    Indices:
        CHL_anomaly_Gigantes = CHL_Gigantes − 30-day rolling mean CHL_Gigantes
        CHL_anomaly_Roxas    = CHL_Roxas    − 30-day rolling mean CHL_Roxas
        SST_stress_Gigantes  = max(0, thetao_Gigantes − SST_STRESS_THRESHOLD)
        SST_stress_Roxas     = max(0, thetao_Roxas    − SST_STRESS_THRESHOLD)

    Args:
        wide: DataFrame after add_rolling_features().

    Returns:
        wide with CHL_anomaly_* and SST_stress_* columns.
    """
    wide = wide.copy()
    for loc in ("Gigantes", "Roxas"):
        roll30_col = f"CHL_{loc}_roll30mean"
        chl_col    = f"CHL_{loc}"
        sst_col    = f"thetao_{loc}"

        if chl_col in wide.columns and roll30_col in wide.columns:
            wide[f"CHL_anomaly_{loc}"] = wide[chl_col] - wide[roll30_col]

        if sst_col in wide.columns:
            wide[f"SST_stress_{loc}"] = (
                (wide[sst_col] - SST_STRESS_THRESHOLD).clip(lower=0.0)
            )
    return wide


# ---------------------------------------------------------------------------
# Step 6: Imputation flags from mask.csv
# ---------------------------------------------------------------------------

def add_imputation_flags(wide: pd.DataFrame, mask_df: pd.DataFrame) -> pd.DataFrame:
    """
    Append binary was_imputed_<variable>_<location> columns indicating
    whether each cell was artificially masked (and therefore imputed).

    These flags expose the imputation footprint to XGBoost as explicit
    features, allowing the model to down-weight or contextualise imputed
    values during prediction.

    Args:
        wide    : Wide-format feature DataFrame with DatetimeIndex.
        mask_df : Long-format mask DataFrame.
                  Columns: [Location_Name, Date, CHL, mlotst, ...] where
                  True means the cell was masked.

    Returns:
        wide with additional was_imputed_* columns (int 0/1).
    """
    wide = wide.copy()
    mask_df = mask_df.copy()
    mask_df["Date"] = pd.to_datetime(mask_df["Date"])

    for var in VARIABLES:
        if var not in mask_df.columns:
            continue
        for loc, abbrev in {GIGANTES: "Gigantes", ROXAS: "Roxas"}.items():
            loc_mask = (
                mask_df[mask_df["Location_Name"] == loc][["Date", var]]
                .rename(columns={var: f"was_imputed_{var}_{abbrev}"})
                .set_index("Date")
            )
            # Cast to int; missing rows default to 0 (not imputed)
            loc_mask = loc_mask.astype(int)
            wide = wide.join(loc_mask, how="left")
            flag_col = f"was_imputed_{var}_{abbrev}"
            wide[flag_col] = wide[flag_col].fillna(0).astype(int)

    return wide


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------

def build_feature_matrix(
    imputed_df: pd.DataFrame,
    mask_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Full feature engineering pipeline applied to one imputed dataset.

    Steps executed in order:
        1. Pivot long → wide
        2. Spatial differences
        3. Rolling statistics (no look-ahead)
        4. Calendar features
        5. Derived domain indices
        6. Imputation flags

    Args:
        imputed_df : Fully imputed long-format DataFrame.
        mask_df    : Long-format mask DataFrame (True = was masked).

    Returns:
        Wide-format feature DataFrame ready for XGBoost.
        Target column is 'CHL_Gigantes'.
        Index is DatetimeIndex (daily frequency).
    """
    wide = pivot_to_wide(imputed_df)
    wide = add_spatial_differences(wide)
    wide = add_rolling_features(wide)
    wide = add_calendar_features(wide)
    wide = add_derived_indices(wide)
    wide = add_imputation_flags(wide, mask_df)
    return wide


def get_feature_columns(feature_matrix: pd.DataFrame) -> list[str]:
    """
    Return the list of feature columns (excludes the target 'CHL_Gigantes').

    Args:
        feature_matrix: Output of build_feature_matrix().

    Returns:
        Sorted list of feature column names.
    """
    target = "CHL_Gigantes"
    return [c for c in feature_matrix.columns if c != target]


def get_train_test_split(
    feature_matrix: pd.DataFrame,
    cutoff_date: str,
    test_start: str,
    test_end: str,
    target: str = "CHL_Gigantes",
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Perform a temporal train/test split using rolling-origin boundaries
    defined in Task 1's rolling_origin split config.json files.

    Train : all rows with Date <= cutoff_date
    Test  : rows where test_start <= Date <= test_end

    Args:
        feature_matrix : Wide feature DataFrame with DatetimeIndex.
        cutoff_date    : Last date in training window (inclusive).
        test_start     : First date of test window (inclusive).
        test_end       : Last date of test window (inclusive).
        target         : Target column name (default: 'CHL_Gigantes').

    Returns:
        X_train, y_train, X_test, y_test — all NaN rows in target dropped.
    """
    feat_cols = get_feature_columns(feature_matrix)

    cutoff  = pd.Timestamp(cutoff_date)
    t_start = pd.Timestamp(test_start)
    t_end   = pd.Timestamp(test_end)

    train_df = feature_matrix.loc[feature_matrix.index <= cutoff].copy()
    test_df  = feature_matrix.loc[
        (feature_matrix.index >= t_start) & (feature_matrix.index <= t_end)
    ].copy()

    # Drop rows where the target itself is still NaN
    train_df = train_df.dropna(subset=[target])
    test_df  = test_df.dropna(subset=[target])

    # Fill remaining NaN features with 0 (rare edge case after imputation)
    train_df[feat_cols] = train_df[feat_cols].fillna(0.0)
    test_df[feat_cols]  = test_df[feat_cols].fillna(0.0)

    X_train = train_df[feat_cols]
    y_train = train_df[target]
    X_test  = test_df[feat_cols]
    y_test  = test_df[target]

    return X_train, y_train, X_test, y_test
