"""
threshold_analysis.py
======================
Decision-threshold sweep for each base model and the weighted-average
ensemble.

run_ensemble.py evaluates all models and strategies at the standard 0.5
threshold. This script pools each model's predicted probabilities across
all 6 rolling-origin splits into one sample and sweeps decision thresholds
to show the precision/recall/F1/F2 trade-off at each one.

Usage:
    cd ensemble_model
    python threshold_analysis.py

Output:
    results/threshold_sweep_all_models.csv — full sweep table for every model
    Printed summary per model: best-F1 threshold, best-F2 threshold, and
    values at 0.30 / 0.35.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, fbeta_score, precision_score, recall_score

warnings.filterwarnings("ignore")

_THIS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _THIS_DIR / "code"
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from ensemble_data import DEFAULT_DATASET_PATH, build_splits, load_and_prepare  # noqa: E402
from ensemble_evaluate import compute_metrics  # noqa: E402
from ensemble_inference import predict_all  # noqa: E402
from ensemble_strategies import weighted_avg  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"
SWEEP_CSV = RESULTS_DIR / "threshold_sweep_all_models.csv"

THRESHOLDS = np.unique(np.concatenate([
    np.round(np.arange(0.05, 0.96, 0.05), 2),
    np.round(np.arange(0.20, 0.51, 0.01), 2),
]))


def sweep(y_true: np.ndarray, y_prob: np.ndarray) -> pd.DataFrame:
    rows = []
    for t in THRESHOLDS:
        y_pred = (y_prob >= t).astype(int)
        rows.append({
            "threshold": t,
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1": fbeta_score(y_true, y_pred, beta=1.0, zero_division=0),
            "f2": fbeta_score(y_true, y_pred, beta=2.0, zero_division=0),
        })
    return pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)


def print_summary(model_name: str, sweep_df: pd.DataFrame) -> None:
    best_f1_row = sweep_df.loc[sweep_df["f1"].idxmax()]
    best_f2_row = sweep_df.loc[sweep_df["f2"].idxmax()]

    print(f"\n--- {model_name} ---")
    print(f"Best F1 @ threshold={best_f1_row['threshold']:.2f}: "
          f"precision={best_f1_row['precision']:.4f}, recall={best_f1_row['recall']:.4f}, "
          f"f1={best_f1_row['f1']:.4f}, accuracy={best_f1_row['accuracy']:.4f}")
    print(f"Best F2 @ threshold={best_f2_row['threshold']:.2f}: "
          f"precision={best_f2_row['precision']:.4f}, recall={best_f2_row['recall']:.4f}, "
          f"f2={best_f2_row['f2']:.4f}, accuracy={best_f2_row['accuracy']:.4f}")
    for t in (0.30, 0.35):
        row = sweep_df.loc[np.isclose(sweep_df["threshold"], t)]
        if not row.empty:
            r = row.iloc[0]
            print(f"  threshold={t:.2f}: precision={r['precision']:.4f}, recall={r['recall']:.4f}, "
                  f"f1={r['f1']:.4f}, accuracy={r['accuracy']:.4f}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("HARIBON Decision-Threshold Sweep — all models + ensemble")
    print("=" * 72)

    print("\n[1/3] Loading data and building splits...")
    df = load_and_prepare(str(DEFAULT_DATASET_PATH), imputation_method="hybrid_adaptive")
    splits = build_splits(df)
    print(f"  {len(df):,} rows loaded | {len(splits)} splits")

    print("\n[2/3] Running per-model inference and pooling probabilities...")
    pooled_probs: dict[str, list[float]] = {}
    pooled_labels: dict[str, list[int]] = {}

    for split in splits:
        print(f"  Split {split.split_num} ({split.test_start} to {split.test_end})")
        probs = predict_all(split_data=split, transformer_scenario="hybrid_adaptive")

        auc_weights = {}
        for model, model_probs in probs.items():
            m = compute_metrics(split.y_test, model_probs)
            auc_weights[model] = float(m["auc"]) if not np.isnan(m["auc"]) else 0.0

        probs["weighted_avg"] = weighted_avg(probs, auc_weights)

        for model, model_probs in probs.items():
            pooled_probs.setdefault(model, []).extend(np.asarray(model_probs).tolist())
            pooled_labels.setdefault(model, []).extend(split.y_test.tolist())

    print("\n[3/3] Sweeping decision thresholds per model...")
    all_sweeps = []
    for model in pooled_probs:
        y_true = np.array(pooled_labels[model])
        y_prob = np.array(pooled_probs[model])
        print(f"\n  {model}: {len(y_true):,} pooled samples "
              f"({int(y_true.sum())} positive, bloom rate={y_true.mean():.3f})")

        sweep_df = sweep(y_true, y_prob)
        sweep_df.insert(0, "model", model)
        all_sweeps.append(sweep_df)

    combined = pd.concat(all_sweeps, ignore_index=True)
    combined.to_csv(SWEEP_CSV, index=False)
    print(f"\n  Saved: {SWEEP_CSV}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for model in pooled_probs:
        model_sweep = combined[combined["model"] == model].reset_index(drop=True)
        print_summary(model, model_sweep)

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
