# pyright: reportMissingImports=false
"""
==============================================================================
Usage:
    cd transformer_model
    python run_transformer.py
    python run_transformer.py --scenarios hybrid_adaptive native_masking
    python run_transformer.py --history-days 45 --epochs 60

Purpose:
    Objective 2 - Task 4 Transformer benchmark on Combined_Labeled.csv
    with two data strategies:
      1) hybrid_adaptive (best-imputation strategy)
      2) native_masking (no imputation)

Outputs:
    transformer_model/results/
      - transformer_per_split_metrics.csv
      - transformer_summary.csv
      - transformer_hybrid_vs_native.csv
==============================================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _THIS_DIR / "code"
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from data_pipeline import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    generate_rolling_origin_splits,
    load_final_dataset,
    make_sequence_dataset_for_split,
    prepare_scenario_dataframe,
)  # type: ignore[reportMissingImports]
from evaluate_results import build_pairwise_comparison, build_summary  # noqa: E402  # type: ignore[reportMissingImports]
from train_eval import TrainConfig, train_and_evaluate_split  # noqa: E402  # type: ignore[reportMissingImports]


SCENARIOS = ["hybrid_adaptive", "native_masking"]
NUM_SPLITS = 4

RESULTS_DIR = _THIS_DIR / "results"
PER_SPLIT_CSV = RESULTS_DIR / "transformer_per_split_metrics.csv"
SUMMARY_CSV = RESULTS_DIR / "transformer_summary.csv"
DELTA_CSV = RESULTS_DIR / "transformer_hybrid_vs_native.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HARIBON Objective 2 - Transformer benchmark",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=SCENARIOS,
        choices=SCENARIOS,
        help="Scenarios to run (default: both)",
    )
    parser.add_argument("--history-days", type=int, default=30)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--ff-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--dataset-path", type=str, default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--num-splits", type=int, default=NUM_SPLITS)
    parser.add_argument("--test-window-days", type=int, default=90)
    parser.add_argument("--min-train-days", type=int, default=365)
    parser.add_argument("--label-threshold", type=float, default=0.5)
    parser.add_argument("--max-linear-gap", type=int, default=14)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = TrainConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        d_model=args.d_model,
        num_heads=args.num_heads,
        num_layers=args.num_layers,
        ff_dim=args.ff_dim,
        dropout=args.dropout,
    )

    base_df = load_final_dataset(args.dataset_path)
    split_template = prepare_scenario_dataframe(
        base_df,
        scenario="native_masking",
        label_threshold=args.label_threshold,
        max_linear_gap=args.max_linear_gap,
    )
    splits = generate_rolling_origin_splits(
        labeled_df=split_template,
        num_splits=args.num_splits,
        test_window_days=args.test_window_days,
        min_train_days=args.min_train_days,
    )

    rows = []

    print("=" * 78)
    print("HARIBON - Objective 2 - Task 4: Transformer Benchmark")
    print(f"Dataset: {args.dataset_path}")
    print("Scenarios:", ", ".join(args.scenarios))
    print(
        "Rolling-origin config:",
        f"splits={len(splits)}, test_window_days={args.test_window_days}, "
        f"min_train_days={args.min_train_days}"
    )
    print("=" * 78)

    for scenario in args.scenarios:
        print(f"\nScenario: {scenario}")

        scenario_df = prepare_scenario_dataframe(
            base_df,
            scenario=scenario,
            label_threshold=args.label_threshold,
            max_linear_gap=args.max_linear_gap,
        )

        for split_cfg in splits:
            ds = make_sequence_dataset_for_split(
                scenario_df=scenario_df,
                split=split_cfg,
                history_days=args.history_days,
            )

            metrics = train_and_evaluate_split(
                X_train=ds["X_train"],
                y_train=ds["y_train"],
                X_test=ds["X_test"],
                y_test=ds["y_test"],
                config=cfg,
                random_seed=42 + split_cfg.split_num,
            )

            row = {
                "scenario": scenario,
                "split_num": split_cfg.split_num,
                "cutoff_date": split_cfg.cutoff_date.date().isoformat(),
                "test_start": split_cfg.test_start.date().isoformat(),
                "test_end": split_cfg.test_end.date().isoformat(),
                "history_days": args.history_days,
                "label_threshold": args.label_threshold,
                "max_linear_gap": args.max_linear_gap,
                **metrics,
            }
            rows.append(row)

            print(
                f"  split {split_cfg.split_num}: "
                f"AUC={metrics['auc']:.4f} | "
                f"F1={metrics['f1']:.4f} | "
                f"Acc={metrics['accuracy']:.4f}"
            )

    per_split_df = pd.DataFrame(rows)
    per_split_df.to_csv(PER_SPLIT_CSV, index=False)

    summary_df = build_summary(per_split_df)
    summary_df.to_csv(SUMMARY_CSV, index=False)

    delta_df = build_pairwise_comparison(summary_df)
    if not delta_df.empty:
        delta_df.to_csv(DELTA_CSV, index=False)

    print("\nSaved:")
    print(f"  - {PER_SPLIT_CSV}")
    print(f"  - {SUMMARY_CSV}")
    if not delta_df.empty:
        print(f"  - {DELTA_CSV}")

    if not summary_df.empty:
        print("\nSummary (sorted by AUC):")
        cols = [
            "rank_auc",
            "scenario",
            "accuracy_mean",
            "f1_mean",
            "auc_mean",
            "n_splits",
        ]
        printable = summary_df[[c for c in cols if c in summary_df.columns]]
        print(printable.to_string(index=False))


if __name__ == "__main__":
    main()
