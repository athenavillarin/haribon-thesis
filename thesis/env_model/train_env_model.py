"""
train_env_model.py
==================
Logistic regression on slow-moving environmental drivers (sea temperature and
rainfall anomalies over 30-90 days, season, ENSO) plus each site's ban history.
Evaluated on the same 6 rolling-origin splits and metrics as
evaluation/baselines.py.

A small linear model is used on purpose: the data hold ~130 ban onsets, and
larger models (XGBoost on ~100 features, LSTM/GRU) fit noise and site identity.

Usage:
    cd env_model
    python train_env_model.py           # rolling-origin splits
    python train_env_model.py --loso    # also leave-one-site-out (environment only)

Output:
    results/env_model_per_split.csv
    results/env_model_summary.csv
    results/env_model_coefficients.csv   (final split, standardized)
    results/env_model_loso.csv           (with --loso)
    saved_model/env_model_split{n}.joblib
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_THIS_DIR = Path(__file__).resolve().parent
for p in (_THIS_DIR.parent / "evaluation", _THIS_DIR.parent / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from baselines import baseline_scores, build_test_frame, score_split, summarize  # noqa: E402
from ensemble_data import DEFAULT_DATASET_PATH, SPLITS, load_and_prepare  # noqa: E402
from features import CORE_FEATURES, PRIOR_FEATURES, build_features, load_daily  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"
MODEL_DIR = _THIS_DIR / "saved_model"

MODEL_FEATURES = CORE_FEATURES + PRIOR_FEATURES
REG_C = 0.1
LOSO_TRAIN_END = "2021-12-31"


def fit_model(train: pd.DataFrame, feature_cols: list[str]) -> Pipeline:
    train = train.dropna(subset=feature_cols)
    model = Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(C=REG_C, max_iter=2000)),
    ])
    model.fit(train[feature_cols], train["target"], lr__sample_weight=train["target_weight"])
    return model


def predict(model: Pipeline, frame: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
    # Missing ONI at the very end of the record is filled with the training mean
    X = frame[feature_cols].fillna(pd.Series(model.named_steps["scale"].mean_, index=feature_cols))
    return model.predict_proba(X)[:, 1]


def run_splits(daily: pd.DataFrame, labeled: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    records, model = [], None
    for cfg in SPLITS:
        feats = build_features(daily, cfg["train_end"])
        train = feats[feats["target_date"] <= pd.Timestamp(cfg["train_end"])]
        test = feats[(feats["target_date"] >= pd.Timestamp(cfg["test_start"]))
                     & (feats["target_date"] <= pd.Timestamp(cfg["test_end"]))]

        model = fit_model(train, MODEL_FEATURES)
        joblib.dump(model, MODEL_DIR / f"env_model_split{cfg['split_num']}.joblib")

        split = SimpleNamespace(
            train_end=cfg["train_end"],
            locs_test=test["Location_Name"].to_numpy(),
            dates_test=test["target_date"].to_numpy(),
            y_test=test["target"].astype(int).to_numpy(),
        )
        frame = build_test_frame(labeled, split)
        scores = baseline_scores(labeled, split, frame)
        scores["history_only"] = predict(fit_model(train, PRIOR_FEATURES), test, PRIOR_FEATURES)
        scores["env_only"] = predict(fit_model(train, CORE_FEATURES), test, CORE_FEATURES)
        scores["env_model"] = predict(model, test, MODEL_FEATURES)

        for row in score_split(frame, scores):
            row["split"] = cfg["split_num"]
            records.append(row)
        env = records[-1]
        print(f"Split {cfg['split_num']}: pooled={env['pooled_auc']:.3f}  "
              f"per_site={env['per_site_auc']:.3f}  onset14={env['onset_auc_14d']:.3f}")

    coefs = pd.DataFrame({
        "feature": MODEL_FEATURES,
        "coefficient": model.named_steps["lr"].coef_[0],
    }).sort_values("coefficient", key=np.abs, ascending=False)
    return pd.DataFrame(records), coefs


def run_loso(daily: pd.DataFrame) -> pd.DataFrame:
    """Environment-only model trained on six sites up to LOSO_TRAIN_END and
    tested on the seventh site after it, so neither the site nor the test
    period is seen in training. Site-history features are left out: an unseen
    site has no ban history.
    """
    feats = build_features(daily, LOSO_TRAIN_END)
    is_train = feats["target_date"] <= pd.Timestamp(LOSO_TRAIN_END)
    rows = []
    for site in feats["Location_Name"].unique():
        at_site = feats["Location_Name"] == site
        train, test = feats[~at_site & is_train], feats[at_site & ~is_train]
        p = predict(fit_model(train, CORE_FEATURES), test, CORE_FEATURES)
        y = test["target"].to_numpy()
        auc = roc_auc_score(y, p) if len(np.unique(y)) == 2 else float("nan")
        rows.append({"held_out_site": site, "auc": auc, "positive_rate": y.mean(), "n": len(y)})
        print(f"LOSO {site:20s} auc={auc:.3f}  positive_rate={y.mean():.3f}")
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the environment-driven HAB model.")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--loso", action="store_true", help="Also run leave-one-site-out.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    daily = load_daily(args.dataset_path)
    labeled = load_and_prepare(args.dataset_path, imputation_method="hybrid_adaptive")

    per_split, coefs = run_splits(daily, labeled)
    summarize(per_split, RESULTS_DIR, "env_model")
    coefs.to_csv(RESULTS_DIR / "env_model_coefficients.csv", index=False)

    print("\nStandardized coefficients (final split):")
    print(coefs.round(3).to_string(index=False))

    if args.loso:
        run_loso(daily).to_csv(RESULTS_DIR / "env_model_loso.csv", index=False)


if __name__ == "__main__":
    main()
