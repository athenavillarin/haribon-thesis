"""
compare_drivers.py
==================
Tests whether environmental parameters beyond sea temperature and rainfall
improve the logistic regression. Every parameter gets the same treatment
(site-relative anomaly, 30/60/90-day rolling means), and each set is scored on
the same 6 rolling-origin splits and rows as the deployed model.

Sets compared:
    current          sea temperature + rainfall (deployed)
    current + <x>    one extra parameter at a time
    all              all 11 parameters
Each set is scored with and without the site ban-history features.

Usage:
    cd env_model
    python compare_drivers.py

Output:
    results/compare_drivers_per_split.csv
    results/compare_drivers_summary.csv
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
for p in (_THIS_DIR.parent / "evaluation", _THIS_DIR.parent / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from baselines import build_test_frame, score_split, summarize  # noqa: E402
from ensemble_data import DEFAULT_DATASET_PATH, SPLITS, load_and_prepare  # noqa: E402
from features import ALL_DRIVERS, DRIVERS, PRIOR_FEATURES, SKEWED_DRIVERS, build_features, core_features, load_daily  # noqa: E402
from train_env_model import fit_model, predict  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"


def driver_sets() -> dict[str, list[str]]:
    sets = {"current": DRIVERS}
    for extra in ALL_DRIVERS:
        if extra not in DRIVERS:
            sets[f"current+{extra}"] = DRIVERS + [extra]
    sets["all"] = ALL_DRIVERS
    return sets


def main() -> None:
    daily = load_daily(DEFAULT_DATASET_PATH, log_drivers=SKEWED_DRIVERS)
    labeled = load_and_prepare(DEFAULT_DATASET_PATH, imputation_method="hybrid_adaptive")
    sets = driver_sets()

    records = []
    for cfg in SPLITS:
        feats = build_features(daily, cfg["train_end"], drivers=ALL_DRIVERS)
        train = feats[feats["target_date"] <= pd.Timestamp(cfg["train_end"])]
        test = feats[(feats["target_date"] >= pd.Timestamp(cfg["test_start"]))
                     & (feats["target_date"] <= pd.Timestamp(cfg["test_end"]))]
        split = SimpleNamespace(
            train_end=cfg["train_end"],
            locs_test=test["Location_Name"].to_numpy(),
            dates_test=test["target_date"].to_numpy(),
            y_test=test["target"].astype(int).to_numpy(),
        )
        frame = build_test_frame(labeled, split)

        scores = {}
        for name, drivers in sets.items():
            env = core_features(drivers)
            scores[f"{name} | env only"] = predict(fit_model(train, env), test, env)
            scores[f"{name} | with history"] = predict(fit_model(train, env + PRIOR_FEATURES), test, env + PRIOR_FEATURES)
        for row in score_split(frame, scores):
            row["split"] = cfg["split_num"]
            records.append(row)
        print(f"Split {cfg['split_num']} done", flush=True)

    summarize(pd.DataFrame(records), RESULTS_DIR, "compare_drivers")
    summary = pd.read_csv(RESULTS_DIR / "compare_drivers_summary.csv")
    cols = ["model", "pooled_auc_mean", "per_site_auc_mean", "onset_auc_14d_mean", "f1_mean"]
    print(summary[summary["model"].str.contains(r"\|")][cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
