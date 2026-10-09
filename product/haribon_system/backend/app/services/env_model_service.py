"""
Environment-driven red tide model for the daily forecast.

Loads the exported model (artifacts/best_model/env_model/env_model.json) and
scores today for a site. Sea temperature and rainfall history come from
Combined_Labeled_2_0.csv; the days after it ends are fetched live with the
same sampling points as training (SITES and MATCHED_CELLS in
thesis/final_compiled_dataset/fetch_site_environment.py).
Features are built with the training code (thesis/env_model/features.py) and
the training cutoff, so they match what the model was trained on.
"""

from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "artifacts" / "THESIS_WINNERS.json").exists():
            return parent
    raise FileNotFoundError("Could not locate the repository root (artifacts/THESIS_WINNERS.json)")


REPO_ROOT = _repo_root()
MODEL_PATH = REPO_ROOT / "artifacts" / "best_model" / "env_model" / "env_model.json"
DATASET_DIR = REPO_ROOT / "thesis" / "final_compiled_dataset"

for _path in (REPO_ROOT / "thesis" / "env_model", DATASET_DIR, REPO_ROOT / "thesis" / "ensemble_model" / "code"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


@functools.lru_cache(maxsize=1)
def load_bundle() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def _history_grid() -> pd.DataFrame:
    from features import load_grid
    return load_grid(DATASET_DIR / load_bundle()["dataset"])


def predict_site(location: str, today: pd.Timestamp) -> dict:
    """Probability that `location` is under a shellfish ban tomorrow, with the inputs used."""
    from features import DRIVERS, build_features, load_daily
    from fetch_site_environment import SITES, fetch_recent_drivers

    bundle = load_bundle()
    today = pd.Timestamp(today).tz_localize(None).normalize()
    history = _history_grid()
    history = history[history["Location_Name"] == location]
    if history.empty or location not in SITES:
        raise ValueError(f"{location} is not in {bundle['dataset']}")
    lat, lon = SITES[location]

    recent_start = history["Date"].max() + pd.Timedelta(days=1)
    recent = pd.DataFrame()
    precip_sources = {}
    if recent_start <= today:
        fetched = fetch_recent_drivers(lat, lon, recent_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        precip_sources = fetched["precip_source"].fillna("missing").value_counts().to_dict()
        recent = fetched[DRIVERS].reset_index()
        recent["Location_Name"] = location
        recent["Month"] = recent["Date"].dt.month
        # Days no source has published yet get the site's monthly mean rather than a copy of the previous day
        monthly_mean = history.groupby("Month")[DRIVERS].mean()
        recent[DRIVERS] = recent[DRIVERS].fillna(
            pd.DataFrame(monthly_mean.reindex(recent["Month"]).to_numpy(), columns=DRIVERS, index=recent.index))

    grid = pd.concat([history, recent], ignore_index=True)
    daily = load_daily(grid=grid)
    feats = build_features(daily, bundle["trained_through"], keep_unlabeled=True)
    row = feats[feats["Date"] == today]
    if row.empty:
        raise ValueError(f"No feature row for {location} on {today.date()}")

    mean = np.array(bundle["scaler_mean"])
    x = row[bundle["features"]].iloc[0].to_numpy(dtype=float)
    x = np.where(np.isnan(x), mean, x)
    z = (x - mean) / np.array(bundle["scaler_scale"])
    probability = float(1.0 / (1.0 + np.exp(-(z @ np.array(bundle["coef"]) + bundle["intercept"]))))

    return {
        "probability": probability,
        "features": {name: round(float(v), 4) for name, v in zip(bundle["features"], x)},
        "precip_sources": precip_sources,
        "history_through": str(history["Date"].max().date()),
        "trained_through": bundle["trained_through"],
    }
