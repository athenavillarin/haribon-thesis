"""
==============================================================================
HARIBON Objective 2 — Task 5: Ensemble Model
==============================================================================
Usage:
    cd ensemble_model
    python run_ensemble.py

    # Run specific strategies only
    python run_ensemble.py --strategies soft_vote weighted_avg

    # Run specific splits only
    python run_ensemble.py --splits 1 2

    # Custom dataset path
    python run_ensemble.py --dataset-path ../final_compiled_dataset/Combined_Labeled.csv

Purpose:
    Combines XGBoost, LSTM, GRU, and Transformer predictions using three
    ensemble strategies on 4 common rolling-origin splits, then:
      1. Compares all individual models and ensemble strategies by AUC-ROC
      2. Compiles the full Objective 2 model comparison table

Outputs (saved to ensemble_model/results/):
    ensemble_per_split_metrics.csv  — per-split metrics for each model & strategy
    ensemble_summary.csv            — mean ± std across 4 splits, ranked by AUC
    obj2_model_comparison_final.csv — final Obj 2 comparison table
==============================================================================
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_THIS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _THIS_DIR / "code"
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from ensemble_data import (  # noqa: E402  # type: ignore[reportMissingImports]
    DEFAULT_DATASET_PATH,
    IMPUTATION_METHODS,
    build_splits,
    load_and_prepare,
)
from ensemble_evaluate import (  # noqa: E402  # type: ignore[reportMissingImports]
    build_obj2_comparison,
    build_per_split_records,
    build_summary,
    compute_metrics,
    print_obj2_comparison,
    print_summary_table,
)
from ensemble_inference import predict_all  # noqa: E402  # type: ignore[reportMissingImports]
from ensemble_strategies import apply_all_strategies, stacked  # noqa: E402  # type: ignore[reportMissingImports]

RESULTS_DIR      = _THIS_DIR / "results"
PER_SPLIT_CSV    = RESULTS_DIR / "ensemble_per_split_metrics.csv"
SUMMARY_CSV      = RESULTS_DIR / "ensemble_summary.csv"
OBJ2_COMPARE_CSV = RESULTS_DIR / "obj2_model_comparison_final.csv"

ALL_STRATEGIES = ["soft_vote", "weighted_avg", "stacked"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HARIBON Obj 2 Task 5 — Ensemble model runner",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=ALL_STRATEGIES,
        choices=ALL_STRATEGIES,
        help="Ensemble strategies to evaluate (default: all three)",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4],
        choices=[1, 2, 3, 4],
        help="Which rolling-origin splits to run (default: 1 2 3 4)",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=str(DEFAULT_DATASET_PATH),
        help="Path to Combined_Labeled.csv",
    )
    parser.add_argument(
        "--imputation-method",
        type=str,
        default="hybrid_adaptive",
        choices=IMPUTATION_METHODS,
        help="Imputation method to apply before classification (default: hybrid_adaptive)",
    )
    parser.add_argument(
        "--all-imputation-methods",
        action="store_true",
        help="Run the full benchmark for all supported imputation methods",
    )
    parser.add_argument(
        "--transformer-scenario",
        type=str,
        default="hybrid_adaptive",
        choices=["native_masking", "hybrid_adaptive"],
        help="Which Transformer scenario to use for inference (default: hybrid_adaptive)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    imputation_methods = IMPUTATION_METHODS if args.all_imputation_methods else [args.imputation_method]

    print("=" * 72)
    print("HARIBON Objective 2 -- Task 5: Ensemble Model")
    print("=" * 72)
    print(f"Dataset   : {args.dataset_path}")
    print(f"Splits    : {args.splits}")
    print(f"Strategies: {args.strategies}")
    print(f"Imputation methods: {imputation_methods}")
    print(f"Transformer scenario: {args.transformer_scenario}")
    print("=" * 72)
    all_per_split_frames: list[pd.DataFrame] = []
    all_summary_frames: list[pd.DataFrame] = []
    all_obj2_frames: list[pd.DataFrame] = []

    for imputation_method in imputation_methods:
        # ------------------------------------------------------------------
        # Phase 1: Load data & build splits
        # ------------------------------------------------------------------
        print(f"\n[Phase 1] Loading data and building splits ({imputation_method})...")
        df = load_and_prepare(args.dataset_path, imputation_method=imputation_method)
        all_splits = build_splits(df)
        # Filter to requested splits
        splits = [s for s in all_splits if s.split_num in args.splits]
        print(f"  Loaded {len(df):,} rows | {len(splits)} splits active")
        for s in splits:
            print(f"  Split {s.split_num}: train <={s.train_end} | "
                  f"test {s.test_start} to {s.test_end} | "
                  f"n_train={s.X_seq_train.shape[0]:,} | "
                  f"n_test={s.X_seq_test.shape[0]:,} | "
                  f"bloom_rate={float(np.mean(s.y_test)):.3f}")

        # ------------------------------------------------------------------
        # Phase 2: Per-model inference on each split
        # ------------------------------------------------------------------
        print("\n[Phase 2] Running per-model inference...")
        all_probs: list[dict] = []   # one dict per split
        all_y_test: list[np.ndarray] = []

        for split in splits:
            print(f"\n  Split {split.split_num} ({split.test_start} to {split.test_end})")
            probs = predict_all(
                split_data=split,
                transformer_scenario=args.transformer_scenario,
            )
            all_probs.append(probs)
            all_y_test.append(split.y_test)

        # ------------------------------------------------------------------
        # Phase 3: Ensemble strategies
        # ------------------------------------------------------------------
        print("\n[Phase 3] Applying ensemble strategies...")
        all_strategy_probs: list[dict] = []

        # Pre-compute per-split AUC weights for weighted_avg
        for i, (split, probs) in enumerate(zip(splits, all_probs)):
            auc_weights = {}
            for model, model_probs in probs.items():
                m = compute_metrics(split.y_test, model_probs)
                auc_w = m["auc"]
                auc_weights[model] = float(auc_w) if not np.isnan(auc_w) else 0.0

            # Stacking: leave-one-out across all available splits
            stacked_probs = None
            if "stacked" in args.strategies and len(splits) > 1:
                stacked_probs = stacked(
                    target_split_idx=i,
                    all_split_probs=all_probs,
                    all_y_test=all_y_test,
                )

            strategy_probs = apply_all_strategies(
                probs_dict=probs,
                auc_weights=auc_weights,
                stacked_probs=stacked_probs if "stacked" in args.strategies else None,
            )
            # Keep only requested strategies
            strategy_probs = {k: v for k, v in strategy_probs.items() if k in args.strategies}
            all_strategy_probs.append(strategy_probs)

        # ------------------------------------------------------------------
        # Phase 4: Evaluation
        # ------------------------------------------------------------------
        print("\n[Phase 4] Computing metrics...")
        split_results = []
        for split, probs, strat_probs in zip(splits, all_probs, all_strategy_probs):
            split_results.append({
                "split_num":      split.split_num,
                "train_end":      split.train_end,
                "test_start":     split.test_start,
                "test_end":       split.test_end,
                "n_train":        int(split.X_seq_train.shape[0]),
                "n_test":         int(split.X_seq_test.shape[0]),
                "y_test":         split.y_test,
                "model_probs":    probs,
                "strategy_probs": strat_probs,
            })

        per_split_df = build_per_split_records(split_results)
        per_split_df["imputation_method"] = imputation_method
        all_per_split_frames.append(per_split_df)

        summary_df = build_summary(per_split_df)
        summary_df["imputation_method"] = imputation_method
        all_summary_frames.append(summary_df)

        obj2_df = build_obj2_comparison(summary_df)
        obj2_df["imputation_method"] = imputation_method
        all_obj2_frames.append(obj2_df)

    per_split_out = pd.concat(all_per_split_frames, ignore_index=True) if all_per_split_frames else pd.DataFrame()
    per_split_out.to_csv(PER_SPLIT_CSV, index=False)
    print(f"  Saved: {PER_SPLIT_CSV}")

    summary_out = pd.concat(all_summary_frames, ignore_index=True) if all_summary_frames else pd.DataFrame()
    summary_out.to_csv(SUMMARY_CSV, index=False)
    print(f"  Saved: {SUMMARY_CSV}")

    obj2_out = pd.concat(all_obj2_frames, ignore_index=True) if all_obj2_frames else pd.DataFrame()
    if not obj2_out.empty:
        obj2_out = obj2_out.sort_values(
            ["auc_mean", "f1_mean", "recall_mean"],
            ascending=[False, False, False],
            na_position="last",
        ).reset_index(drop=True)
        obj2_out.insert(0, "overall_rank", range(1, len(obj2_out) + 1))
    obj2_out.to_csv(OBJ2_COMPARE_CSV, index=False)
    print(f"  Saved: {OBJ2_COMPARE_CSV}")

    # ------------------------------------------------------------------
    # Print results
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("ENSEMBLE RESULTS -- Per-model & strategy (mean +/- std, sorted by AUC)")
    print("=" * 72)
    if len(imputation_methods) == 1:
        print_summary_table(summary_out)
    else:
        for method in imputation_methods:
            print(f"\nImputation method: {method}")
            print_summary_table(summary_out[summary_out["imputation_method"] == method])

    print("\n" + "=" * 72)
    print("OBJECTIVE 2 FINAL MODEL COMPARISON")
    print("=" * 72)
    if len(imputation_methods) == 1:
        print_obj2_comparison(obj2_out)
    else:
        for method in imputation_methods:
            print(f"\nImputation method: {method}")
            print_obj2_comparison(obj2_out[obj2_out["imputation_method"] == method])

    # Identify best overall
    best_row = obj2_out.iloc[0]
    print(
        f"\n★  Best model: {best_row['model']}  |  "
        f"Imputation = {best_row['imputation_method']}  |  "
        f"AUC = {best_row['auc_mean']:.4f}"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
