"""
features.py
===========
Environmental feature builder that removes site fingerprints.

Every variable is turned into a site-relative anomaly: the value minus the
site's monthly climatology, divided by the site's standard deviation. Both
statistics come from training dates only. On top of the anomalies we add
causal rolling means, lagged rolling means and 7-day changes, so the model
can learn the delay between conditions and announced shellfish bans
(lab testing takes ~2 weeks).

Label weighting reflects that delay: the 14 days before a ban starts and the
last 14 days of a ban are uncertain and get low weight; days with a real
bulletin get extra weight.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_ENSEMBLE_CODE_DIR = _THIS_DIR.parent / "ensemble_model" / "code"
if str(_ENSEMBLE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENSEMBLE_CODE_DIR))

from ensemble_data import DEFAULT_DATASET_PATH, FEATURES, TARGET, _impute_df  # noqa: E402

ONI_PATH = _THIS_DIR.parent / "final_compiled_dataset" / "oni_monthly.csv"

LOG_FEATURES = ["CHL", "precip_mm_day"]
DRIVERS = ["CHL", "thetao", "so", "mlotst", "NDVI_daily", "precip_mm_day", "wind_speed_ms"]
ROLL_WINDOWS = (7, 14, 30, 60, 90)
LAGS = (7, 14, 21)
ONI_LAG_MONTHS = 2  # ONI for month m is published after month m+1 ends

LABEL_DELAY_DAYS = 14
UNCERTAIN_WEIGHT = 0.3
BULLETIN_WEIGHT = 3.0

# Slow-moving drivers with a consistent within-site signal, plus season and ENSO
CORE_FEATURES = [
    "thetao_roll30", "thetao_roll60", "thetao_roll90",
    "precip_mm_day_roll30", "precip_mm_day_roll60", "precip_mm_day_roll90",
    "doy_sin", "doy_cos", "oni",
]
# Each site's ban history from training dates only
PRIOR_FEATURES = ["clim_rate", "site_rate_365"]


def load_daily(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load the full daily grid (including unlabeled days) and impute features."""
    df = pd.read_csv(dataset_path, parse_dates=["Date"])
    # Reindex to a gap-free daily grid so row shifts and rolling windows are in days
    full = pd.MultiIndex.from_product(
        [df["Location_Name"].unique(), pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")],
        names=["Location_Name", "Date"],
    )
    df = df.set_index(["Location_Name", "Date"]).reindex(full).reset_index()
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df = _impute_df(df, FEATURES, method="hybrid_adaptive")
    for col in LOG_FEATURES:
        df[col] = np.log1p(df[col].clip(lower=0))
    df["red_tide_binary"] = np.where(df[TARGET].isna(), np.nan, (df[TARGET] >= 0.5).astype(float))
    return df


def _sample_weights(df: pd.DataFrame) -> pd.Series:
    """Weight each row by how much we trust its label, given the ~2-week testing delay."""
    weights = pd.Series(1.0, index=df.index)
    for _, g in df.groupby("Location_Name", sort=False):
        y = g["red_tide_binary"].fillna(0).to_numpy()
        n = len(y)
        w = np.ones(n)
        # Before a ban starts the bloom may already be present; before a ban is
        # lifted the bloom may already be gone. Both windows are down-weighted.
        for c in np.flatnonzero(np.diff(y) != 0) + 1:
            w[max(0, c - LABEL_DELAY_DAYS):c] = UNCERTAIN_WEIGHT
        bulletin = g["red_tide"].notna().to_numpy()
        w[bulletin] = BULLETIN_WEIGHT
        weights.loc[g.index] = w
    return weights


def _oni_column(dates: pd.Series) -> np.ndarray:
    oni = pd.read_csv(ONI_PATH)
    oni["period"] = pd.PeriodIndex.from_fields(year=oni["year"], month=oni["month"], freq="M")
    lookup = oni.set_index("period")["oni"]
    periods = dates.dt.to_period("M") - ONI_LAG_MONTHS
    return lookup.reindex(periods).to_numpy()


def build_features(df: pd.DataFrame, train_end: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Return df with feature columns and the next-day target attached.

    Climatology and scale use only rows dated on or before `train_end`.
    Features on day t predict the label on day t+1.
    """
    df = df.copy()
    train = df[df["Date"] <= pd.Timestamp(train_end)]
    clim = train.groupby(["Location_Name", "Month"])[FEATURES].mean()
    scale = train.groupby("Location_Name")[FEATURES].std().replace(0, 1)

    keys = pd.MultiIndex.from_arrays([df["Location_Name"], df["Month"]])
    anom = (df[FEATURES].to_numpy() - clim.reindex(keys).to_numpy()) \
        / scale.reindex(df["Location_Name"]).to_numpy()
    anom_cols = [f"{f}_anom" for f in FEATURES]
    df[anom_cols] = anom

    new_cols = {}
    grouped = df.groupby("Location_Name", sort=False)
    for f in DRIVERS:
        col = grouped[f"{f}_anom"]
        for w in ROLL_WINDOWS:
            new_cols[f"{f}_roll{w}"] = col.transform(lambda s, w=w: s.rolling(w, min_periods=1).mean())
        roll7 = new_cols[f"{f}_roll7"]
        for lag in LAGS:
            new_cols[f"{f}_roll7_lag{lag}"] = roll7.groupby(df["Location_Name"]).shift(lag)
        new_cols[f"{f}_chg7"] = roll7 - new_cols[f"{f}_roll7_lag7"]

    wind_stress = df["wind_speed_ms"] ** 2
    new_cols["wind_stress_roll7"] = wind_stress.groupby(df["Location_Name"]).transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    ) / scale.reindex(df["Location_Name"])["wind_speed_ms"].to_numpy() ** 2

    doy = df["Date"].dt.dayofyear
    new_cols["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    new_cols["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    new_cols["oni"] = _oni_column(df["Date"])

    df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)
    feature_cols = anom_cols + list(new_cols)

    df["sample_weight"] = _sample_weights(df)
    nxt = df.groupby("Location_Name", sort=False)
    df["target_date"] = nxt["Date"].shift(-1)
    df["target"] = nxt["red_tide_binary"].shift(-1)
    df["target_weight"] = nxt["sample_weight"].shift(-1)
    df = df.dropna(subset=["target"]).reset_index(drop=True)

    labeled = train.dropna(subset=["red_tide_binary"])
    month_rate = labeled.groupby(["Location_Name", "Month"])["red_tide_binary"].mean()
    recent = labeled[labeled["Date"] > pd.Timestamp(train_end) - pd.Timedelta(days=365)]
    site_rate = recent.groupby("Location_Name")["red_tide_binary"].mean()
    month_keys = list(zip(df["Location_Name"], df["target_date"].dt.month))
    df["clim_rate"] = month_rate.reindex(month_keys).fillna(0).to_numpy()
    df["site_rate_365"] = df["Location_Name"].map(site_rate).fillna(0).to_numpy()
    return df, feature_cols + PRIOR_FEATURES
