"""
==============================================================================
Evaluation & Summary
==============================================================================
Purpose:
    Aggregate per-split XGBoost results into a method-level summary table
    (mean ± std across the 4 rolling-origin splits) and produce the CSV
    that Task 5 requires as input.

Input:
    task4_results/xgboost_results_per_split.csv

Output:
    task4_results/xgboost_results_summary.csv

Task 5 input contract (column schema):
    method_name,
    rmse_mean, rmse_std,
    mae_mean,  mae_std,
    r2_mean,   r2_std,
    f1_mean,   f1_std,
    auc_mean,  auc_std

==============================================================================
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (relative to this file's location → task_4/)
# ---------------------------------------------------------------------------

_THIS_DIR    = Path(__file__).resolve().parent
_TASK4_DIR   = _THIS_DIR.parent
RESULTS_DIR  = _TASK4_DIR / "task4_results"
PER_SPLIT_CSV  = RESULTS_DIR / "xgboost_results_per_split.csv"
SUMMARY_CSV    = RESULTS_DIR / "xgboost_results_summary.csv"

# Metrics aggregated in the summary table
METRIC_COLS: list[str] = ["rmse", "mae", "r2", "f1", "auc"]


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def build_summary(per_split_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-split results to method-level mean and std.

    For each imputation method, compute mean and standard deviation across
    the 4 rolling-origin splits for every metric.  Methods with fewer than
    4 successful splits still contribute (NaN splits are excluded from stats).

    Args:
        per_split_df : DataFrame loaded from xgboost_results_per_split.csv.
                       Required columns: method_name, split_num + METRIC_COLS.

    Returns:
        Summary DataFrame with one row per imputation method, columns:
            method_name,
            rmse_mean, rmse_std,
            mae_mean,  mae_std,
            r2_mean,   r2_std,
            f1_mean,   f1_std,
            auc_mean,  auc_std
        Sorted ascending by rmse_mean (best first).
    """
    agg_funcs = {col: ["mean", "std"] for col in METRIC_COLS}

    summary = (
        per_split_df.groupby("method_name")
        .agg(agg_funcs)
        .round(6)
    )

    # Flatten multi-level columns → rmse_mean, rmse_std, …
    summary.columns = ["_".join(col) for col in summary.columns]
    summary = summary.reset_index()

    # Add split count column (how many splits succeeded per method)
    split_counts = (
        per_split_df.groupby("method_name")["split_num"]
        .count()
        .rename("n_splits")
        .reset_index()
    )
    summary = summary.merge(split_counts, on="method_name", how="left")

    # Enforce column order per Task 5 contract
    ordered_cols = (
        ["method_name"]
        + [f"{m}_{s}" for m in METRIC_COLS for s in ("mean", "std")]
        + ["n_splits"]
    )
    summary = summary[[c for c in ordered_cols if c in summary.columns]]

    # Sort best → worst by RMSE
    summary = summary.sort_values("rmse_mean", ascending=True).reset_index(drop=True)
    summary.insert(0, "rank", summary.index + 1)

    return summary


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_summary_table(summary: pd.DataFrame) -> None:
    """
    Print a formatted ASCII summary table to stdout.

    Args:
        summary: Output of build_summary().
    """
    divider = "=" * 110
    header  = (
        f"{'Rank':>4}  {'Method':<42}  "
        f"{'RMSE':>10}  {'MAE':>10}  {'R²':>8}  "
        f"{'F1':>8}  {'AUC':>8}  {'Splits':>6}"
    )

    print(f"\n{divider}")
    print("TASK 4 — XGBoost Performance Summary (mean ± std, 4 rolling-origin splits)")
    print(f"  Target: CHL_Gigantes  |  Bloom threshold: 1.0 µg/L")
    print(divider)
    print(header)
    print("-" * 110)

    for _, row in summary.iterrows():
        print(
            f"{int(row['rank']):>4}  "
            f"{row['method_name']:<42}  "
            f"{row['rmse_mean']:>6.4f}±{row['rmse_std']:>5.4f}  "
            f"{row['mae_mean']:>6.4f}±{row['mae_std']:>5.4f}  "
            f"{row['r2_mean']:>7.4f}  "
            f"{row['f1_mean']:>7.4f}  "
            f"{row.get('auc_mean', float('nan')):>7.4f}  "
            f"{int(row.get('n_splits', 0)):>6}"
        )

    print(divider)
    best = summary.iloc[0]
    print(
        f"\n  Best method by RMSE: {best['method_name']}"
        f"  (RMSE={best['rmse_mean']:.4f}, R²={best['r2_mean']:.4f})"
    )
    print(
        "  → Full per-split details: task4_results/xgboost_results_per_split.csv"
    )
    print(
        "  → SHAP importance per method: task4_results/shap_importance/"
    )
    print(f"{divider}\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate(per_split_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Load per-split results, aggregate, save summary, and print table.

    Can be called with a DataFrame already in memory (e.g. from
    task4_train_xgboost.run_all()) or will read from disk if None.

    Args:
        per_split_df: Optional pre-loaded per-split results DataFrame.

    Returns:
        summary: Method-level summary DataFrame.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if per_split_df is None:
        if not PER_SPLIT_CSV.exists():
            raise FileNotFoundError(
                f"Per-split results not found: {PER_SPLIT_CSV}\n"
                "Run task4_train_xgboost.run_all() first."
            )
        per_split_df = pd.read_csv(PER_SPLIT_CSV)

    if per_split_df.empty:
        print("[WARN] Per-split results DataFrame is empty — no summary generated.")
        return pd.DataFrame()

    summary = build_summary(per_split_df)
    summary.to_csv(SUMMARY_CSV, index=False)
    print(f"✓ Summary saved → {SUMMARY_CSV}")

    print_summary_table(summary)
    return summary


if __name__ == "__main__":
    evaluate()
