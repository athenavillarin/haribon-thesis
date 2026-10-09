"""
baselines.py
============
Compares the trained models against naive baselines that use no environmental
data, on the same 6 rolling-origin splits used by the ensemble.

Baselines:
  persistence   — yesterday's label
  site_prior    — each site's positive rate over the last 365 days of training
  climatology   — each site's positive rate for the target month in training

Metrics:
  pooled_auc    — AUC over all test rows (rewards telling sites apart)
  per_site_auc  — mean AUC within each site that has both classes in the test year
  onset_auc_7d  — AUC for "a ban starts within 7 days", scored only on days whose
                  previous label is 0 (the early-warning question)
  onset_auc_14d — same with a 14-day horizon

Usage:
    cd evaluation
    python baselines.py              # baselines + saved models
    python baselines.py --no-models  # baselines only

Output:
    results/baseline_comparison_per_split.csv
    results/baseline_comparison_summary.csv
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

_THIS_DIR = Path(__file__).resolve().parent
_ENSEMBLE_CODE_DIR = _THIS_DIR.parent / "ensemble_model" / "code"
if str(_ENSEMBLE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENSEMBLE_CODE_DIR))

from ensemble_data import DEFAULT_DATASET_PATH, build_splits, load_and_prepare  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"
ONSET_HORIZONS = (7, 14)
METRIC_COLS = ["pooled_auc", "per_site_auc", "onset_auc_7d", "onset_auc_14d"]


def _safe_auc(y: np.ndarray, p: np.ndarray) -> float:
    mask = ~np.isnan(p)
    y, p = y[mask], p[mask]
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


def build_test_frame(df: pd.DataFrame, split) -> pd.DataFrame:
    """Test rows with previous-day label and future onset targets attached."""
    labels = df[["Location_Name", "Date", "red_tide_binary"]].sort_values(["Location_Name", "Date"])
    labels = labels.set_index(["Location_Name", "Date"])["red_tide_binary"]

    test = pd.DataFrame({
        "Location_Name": split.locs_test,
        "Date": pd.to_datetime(split.dates_test),
        "y": split.y_test,
    })

    prev_keys = list(zip(test["Location_Name"], test["Date"] - pd.Timedelta(days=1)))
    test["y_prev"] = labels.reindex(prev_keys).to_numpy()

    for h in ONSET_HORIZONS:
        future = np.zeros(len(test))
        for k in range(h):
            keys = list(zip(test["Location_Name"], test["Date"] + pd.Timedelta(days=k)))
            future = np.fmax(future, labels.reindex(keys).fillna(0).to_numpy())
        test[f"onset_{h}d"] = future
    return test


def baseline_scores(df: pd.DataFrame, split, test: pd.DataFrame) -> Dict[str, np.ndarray]:
    train = df[df["Date"] <= pd.Timestamp(split.train_end)]
    recent = train[train["Date"] > pd.Timestamp(split.train_end) - pd.Timedelta(days=365)]

    site_rate = recent.groupby("Location_Name")["red_tide_binary"].mean()
    month_rate = train.groupby(["Location_Name", "Month"])["red_tide_binary"].mean()

    month_keys = list(zip(test["Location_Name"], test["Date"].dt.month))
    return {
        "persistence": test["y_prev"].to_numpy(dtype=float),
        "site_prior": test["Location_Name"].map(site_rate).to_numpy(dtype=float),
        "climatology": month_rate.reindex(month_keys).to_numpy(dtype=float),
    }


def score_split(test: pd.DataFrame, scores: Dict[str, np.ndarray]) -> List[dict]:
    """Score every model on the same rows: those where no model's score is missing."""
    scores = {k: np.asarray(v, dtype=float) for k, v in scores.items()}
    usable = [p for p in scores.values() if not np.all(np.isnan(p))]
    common = ~np.any(np.isnan(np.vstack(usable)), axis=0) & test["y_prev"].notna().to_numpy()
    test = test[common]
    scores = {k: v[common] for k, v in scores.items()}

    rows = []
    y = test["y"].to_numpy()
    not_in_ban = (test["y_prev"] == 0).to_numpy()

    for name, p in scores.items():
        site_aucs = []
        for loc in test["Location_Name"].unique():
            m = (test["Location_Name"] == loc).to_numpy()
            site_aucs.append(_safe_auc(y[m], p[m]))

        row = {
            "model": name,
            "pooled_auc": _safe_auc(y, p),
            "per_site_auc": float(np.nanmean(site_aucs)) if not np.all(np.isnan(site_aucs)) else float("nan"),
            "n_sites_scored": int(np.sum(~np.isnan(site_aucs))),
            "n_rows": int(len(y)),
        }
        for h in ONSET_HORIZONS:
            target = test[f"onset_{h}d"].to_numpy()
            row[f"onset_auc_{h}d"] = _safe_auc(target[not_in_ban], p[not_in_ban])
            row[f"n_onset_pos_{h}d"] = int(target[not_in_ban].sum())
        rows.append(row)
    return rows


def summarize(per_split: pd.DataFrame, out_dir: Path, prefix: str) -> pd.DataFrame:
    """Write per-split and mean/std CSVs, print the means, and return the summary."""
    per_split = per_split[["split", "model"] + METRIC_COLS
                          + [c for c in per_split.columns if c not in METRIC_COLS + ["split", "model"]]]
    summary = per_split.groupby("model", sort=False)[METRIC_COLS].agg(["mean", "std"]).round(4)
    summary.columns = [f"{m}_{s}" for m, s in summary.columns]

    per_split.to_csv(out_dir / f"{prefix}_per_split.csv", index=False)
    summary.to_csv(out_dir / f"{prefix}_summary.csv")

    pd.set_option("display.width", 200)
    print("\nMean across splits:")
    print(per_split.groupby("model", sort=False)[METRIC_COLS].mean().round(3).to_string())
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare models against naive baselines.")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--no-models", action="store_true", help="Score baselines only.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_prepare(args.dataset_path, imputation_method="hybrid_adaptive")
    splits = build_splits(df)

    records = []
    for split in splits:
        print(f"\nSplit {split.split_num} ({split.test_start} to {split.test_end})")
        test = build_test_frame(df, split)
        scores = baseline_scores(df, split, test)

        if not args.no_models:
            from ensemble_inference import predict_all
            scores.update(predict_all(split_data=split))

        for row in score_split(test, scores):
            row["split"] = split.split_num
            records.append(row)

    summarize(pd.DataFrame(records), RESULTS_DIR, "baseline_comparison")


if __name__ == "__main__":
    main()
