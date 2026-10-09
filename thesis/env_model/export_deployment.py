"""
export_deployment.py
====================
Trains the environment-driven model on all of Combined_Labeled_2_0.csv and
writes it to artifacts/best_model/env_model/env_model.json for the daily
forecast.

The model is stored as plain numbers (scaler mean/scale, coefficients,
intercept) so the server does not depend on a pickled scikit-learn version.
Features are rebuilt at inference time with features.build_features, using
the same training cutoff, so they match training exactly.

Usage:
    cd env_model
    python export_deployment.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
for p in (_THIS_DIR.parent / "evaluation", _THIS_DIR.parent / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ensemble_data import DEFAULT_DATASET_PATH  # noqa: E402
from features import build_features, load_daily  # noqa: E402
from train_env_model import MODEL_FEATURES, REG_C, fit_model  # noqa: E402

OUTPUT = _THIS_DIR.parents[1] / "artifacts" / "best_model" / "env_model" / "env_model.json"


def main() -> None:
    daily = load_daily(DEFAULT_DATASET_PATH)
    trained_through = daily["Date"].max()
    feats = build_features(daily, str(trained_through.date()))
    model = fit_model(feats, MODEL_FEATURES)
    scale, lr = model.named_steps["scale"], model.named_steps["lr"]

    bundle = {
        "model_type": "env_logistic",
        "dataset": DEFAULT_DATASET_PATH.name,
        "trained_through": str(trained_through.date()),
        "n_training_rows": int(len(feats)),
        "sites": sorted(feats["Location_Name"].unique()),
        "features": MODEL_FEATURES,
        "scaler_mean": scale.mean_.tolist(),
        "scaler_scale": scale.scale_.tolist(),
        "coef": lr.coef_[0].tolist(),
        "intercept": float(lr.intercept_[0]),
        "regularization_C": REG_C,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print(f"Wrote {OUTPUT} (trained through {bundle['trained_through']}, {bundle['n_training_rows']:,} rows)")
    print(pd.Series(bundle["coef"], index=MODEL_FEATURES).round(3).sort_values(key=abs, ascending=False).to_string())


if __name__ == "__main__":
    main()
