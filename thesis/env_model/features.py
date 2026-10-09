"""
features.py
===========
Environmental feature builder that removes site fingerprints.

Each driver is turned into a site-relative anomaly: the value minus the site's
monthly climatology, divided by the site's standard deviation, both taken from
training dates only. Causal 30/60/90-day rolling means of these anomalies,
season and the ENSO index make up the environmental features.

The site's ban history is added as two features computed only from years before
each row, so training rows never see their own labels.

Label weighting reflects the ~2-week shellfish testing delay: the 14 days before
a ban starts and the last 14 days of a ban get low weight; days with a real
bulletin get extra weight.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_ENSEMBLE_CODE_DIR = _THIS_DIR.parent / "ensemble_model" / "code"
if str(_ENSEMBLE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENSEMBLE_CODE_DIR))

from ensemble_data import DEFAULT_DATASET_PATH, TARGET  # noqa: E402

ONI_PATH = _THIS_DIR.parent / "final_compiled_dataset" / "oni_monthly.csv"

DRIVERS = ["thetao", "precip_mm_day"]
LOG_DRIVERS = ["precip_mm_day"]
ROLL_WINDOWS = (30, 60, 90)
FFILL_LIMIT_DAYS = 14
# ONI for month m is a 3-month mean centred on m, released in early-to-mid m+2
ONI_LAG_MONTHS = 3

LABEL_DELAY_DAYS = 14
UNCERTAIN_WEIGHT = 0.3
BULLETIN_WEIGHT = 3.0

CORE_FEATURES = [f"{d}_roll{w}" for d in DRIVERS for w in ROLL_WINDOWS] + ["doy_sin", "doy_cos", "oni"]
PRIOR_FEATURES = ["clim_rate", "site_rate_365"]


def load_grid(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load every site on a gap-free daily grid, without imputation."""
    df = pd.read_csv(dataset_path, parse_dates=["Date"])
    full = pd.MultiIndex.from_product(
        [df["Location_Name"].unique(), pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")],
        names=["Location_Name", "Date"],
    )
    df = df.set_index(["Location_Name", "Date"]).reindex(full).reset_index()
    df["Month"] = df["Date"].dt.month
    df["red_tide_binary"] = np.where(df[TARGET].isna(), np.nan, (df[TARGET] >= 0.5).astype(float))
    return df


def load_daily(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Daily grid with skewed drivers log-transformed."""
    df = load_grid(dataset_path)
    for col in LOG_DRIVERS:
        df[col] = np.log1p(df[col].clip(lower=0))
    return df


def impute_causal(df: pd.DataFrame, is_train: pd.Series, cols: list[str]) -> pd.DataFrame:
    """Forward-fill short gaps, then fall back to training-period climatology."""
    df[cols] = df.groupby("Location_Name", sort=False)[cols].ffill(limit=FFILL_LIMIT_DAYS)
    train = df[is_train]
    month_mean = train.groupby(["Location_Name", "Month"])[cols].mean()
    site_mean = train.groupby("Location_Name")[cols].mean()
    keys = pd.MultiIndex.from_arrays([df["Location_Name"], df["Month"]])
    df[cols] = df[cols].fillna(pd.DataFrame(month_mean.reindex(keys).to_numpy(), columns=cols, index=df.index))
    df[cols] = df[cols].fillna(pd.DataFrame(site_mean.reindex(df["Location_Name"]).to_numpy(), columns=cols, index=df.index))
    df[cols] = df[cols].fillna(train[cols].mean())
    return df


def _sample_weights(df: pd.DataFrame, is_train: pd.Series) -> np.ndarray:
    """Weight training rows by how much we trust their label, using training labels only."""
    weights = np.ones(len(df))
    delay = pd.Timedelta(days=LABEL_DELAY_DAYS)
    for _, g in df[is_train].groupby("Location_Name", sort=False):
        labeled = g.dropna(subset=["red_tide_binary"])
        y = labeled["red_tide_binary"].to_numpy()
        dates = g["Date"]
        w = np.ones(len(g))
        # Before a ban starts the bloom may already be present; before a ban is
        # lifted the bloom may already be gone. Both windows are down-weighted.
        for change in labeled["Date"].to_numpy()[np.flatnonzero(np.diff(y) != 0) + 1]:
            w[((dates >= change - delay) & (dates < change)).to_numpy()] = UNCERTAIN_WEIGHT
        w[g["red_tide"].notna().to_numpy()] = BULLETIN_WEIGHT
        weights[df.index.get_indexer(g.index)] = w
    return weights


def _oni_column(dates: pd.Series) -> np.ndarray:
    oni = pd.read_csv(ONI_PATH)
    oni["period"] = pd.PeriodIndex.from_fields(year=oni["year"], month=oni["month"], freq="M")
    lookup = oni.set_index("period")["oni"]
    return lookup.reindex(dates.dt.to_period("M") - ONI_LAG_MONTHS).to_numpy()


def _history_priors(df: pd.DataFrame, train_end: pd.Timestamp) -> pd.DataFrame:
    """
    Ban-history features from strictly earlier years.

    A row whose target falls in year Y uses labels from years before
    min(Y, train year + 1): the monthly ban rate over those years and the
    ban rate of the single year before.
    """
    train_year = train_end.year
    labeled = df[(df["Date"] <= train_end) & df["red_tide_binary"].notna()].assign(year=lambda d: d["Date"].dt.year)
    by_year_month = labeled.groupby(["Location_Name", "year", "Month"])["red_tide_binary"].agg(["sum", "count"])
    by_year = labeled.groupby(["Location_Name", "year"])["red_tide_binary"].mean()

    tables = []
    for eff_year in range(labeled["year"].min() + 1, train_year + 2):
        past = by_year_month[by_year_month.index.get_level_values("year") < eff_year]
        rate = past.groupby(["Location_Name", "Month"]).sum()
        rate = (rate["sum"] / rate["count"]).rename("clim_rate").reset_index()
        rate["eff_year"] = eff_year
        last = by_year.xs(eff_year - 1, level="year").rename("site_rate_365")
        tables.append(rate.merge(last, left_on="Location_Name", right_index=True, how="left"))
    priors = pd.concat(tables, ignore_index=True)

    keys = pd.DataFrame({
        "Location_Name": df["Location_Name"].to_numpy(),
        "eff_year": np.minimum(df["target_date"].dt.year, train_year + 1).to_numpy(),
        "Month": df["target_date"].dt.month.to_numpy(),
    })
    return keys.merge(priors, on=["Location_Name", "eff_year", "Month"], how="left")[PRIOR_FEATURES]


def build_features(daily: pd.DataFrame, train_end: str) -> pd.DataFrame:
    """
    Return one row per site-day with CORE_FEATURES, PRIOR_FEATURES, the next-day
    target and its training weight. Every statistic uses dates up to `train_end`.
    """
    train_end = pd.Timestamp(train_end)
    df = daily.copy()
    is_train = df["Date"] <= train_end
    df = impute_causal(df, is_train, DRIVERS)

    train = df[is_train]
    clim = train.groupby(["Location_Name", "Month"])[DRIVERS].mean()
    scale = train.groupby("Location_Name")[DRIVERS].std().replace(0, 1)
    keys = pd.MultiIndex.from_arrays([df["Location_Name"], df["Month"]])
    anom = pd.DataFrame(
        (df[DRIVERS].to_numpy() - clim.reindex(keys).to_numpy()) / scale.reindex(df["Location_Name"]).to_numpy(),
        columns=DRIVERS, index=df.index,
    )
    grouped = anom.groupby(df["Location_Name"], sort=False)
    for d in DRIVERS:
        for w in ROLL_WINDOWS:
            df[f"{d}_roll{w}"] = grouped[d].transform(lambda s, w=w: s.rolling(w, min_periods=1).mean())

    doy = df["Date"].dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    df["oni"] = _oni_column(df["Date"])
    df["sample_weight"] = _sample_weights(df, is_train)

    nxt = df.groupby("Location_Name", sort=False)
    df["target_date"] = nxt["Date"].shift(-1)
    df["target"] = nxt["red_tide_binary"].shift(-1)
    df["target_weight"] = nxt["sample_weight"].shift(-1)
    df = df.dropna(subset=["target"]).reset_index(drop=True)
    df[PRIOR_FEATURES] = _history_priors(df, train_end).to_numpy()
    return df
