"""
==============================================================================
Usage:
    cd task_4
    python run_task4.py                         # run all 11 methods
    python run_task4.py --methods linear_interpolation hybrid_adaptive
    python run_task4.py --evaluate-only         # re-aggregate existing results
    python run_task4.py --help

Output:
    task4_results/
    ├── xgboost_results_per_split.csv   — per method × split metrics
    ├── xgboost_results_summary.csv     — method-level summary (Task 5 input)
    └── feature_importance/
        └── feature_importance_<method>.csv  — top-15 features per method
                                               (gain-based; SHAP if shap installed)

==============================================================================
"""

import argparse
import sys
import time
from datetime import timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure task_4/code/ is on sys.path when run_task4.py is called from task_4/
# ---------------------------------------------------------------------------
_TASK4_DIR = Path(__file__).resolve().parent
_CODE_DIR  = _TASK4_DIR / "code"

if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# ---------------------------------------------------------------------------
# Imports (after path setup)
# ---------------------------------------------------------------------------
from task4_train_xgboost import IMPUTATION_METHODS, run_all    # noqa: E402
from task4_evaluate import evaluate                             # noqa: E402


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="HARIBON Task 4 — XGBoost Downstream Imputation Evaluation",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=None,
        choices=list(IMPUTATION_METHODS.keys()),
        metavar="METHOD",
        help=(
            "Imputation methods to evaluate (default: all 11).\n"
            "Choices:\n"
            + "\n".join(f"  {k}" for k in IMPUTATION_METHODS)
        ),
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help=(
            "Skip training. Read existing xgboost_results_per_split.csv "
            "and regenerate the summary table only."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Orchestrate the full Task 4 pipeline."""
    args = parse_args()

    print("=" * 70)
    print("  HARIBON — Task 4: XGBoost Downstream Imputation Evaluation")
    print("=" * 70)

    # ── Evaluate-only mode ────────────────────────────────────────────────
    if args.evaluate_only:
        print("\n[evaluate-only] Skipping training — reading existing results.\n")
        evaluate()
        return

    # ── Select methods ────────────────────────────────────────────────────
    if args.methods:
        selected = {k: IMPUTATION_METHODS[k] for k in args.methods}
        print(f"\nRunning {len(selected)} selected method(s):")
    else:
        selected = IMPUTATION_METHODS
        print(f"\nRunning all {len(selected)} imputation methods:")

    for k, v in selected.items():
        print(f"  • {k:<38} → {v}")

    print(f"\nValidation: rolling_origin splits 1–4 (90-day test windows)")
    print(f"Target    : CHL_Gigantes (Chlorophyll-a, µg/L)")
    print(f"XGBoost   : reg:squarederror  |  max_depth=6  |  lr=0.05\n")

    # ── Training loop ─────────────────────────────────────────────────────
    t0 = time.perf_counter()
    per_split_df = run_all(methods=selected)
    elapsed = timedelta(seconds=int(time.perf_counter() - t0))

    print(f"\n── Training complete in {elapsed} ──")

    # ── Aggregation & summary ─────────────────────────────────────────────
    if not per_split_df.empty:
        evaluate(per_split_df)
    else:
        print("[WARN] No results to summarise.")

    print("Task 4 complete.")


if __name__ == "__main__":
    main()
