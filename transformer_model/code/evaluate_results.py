"""
Aggregate and compare Transformer results across scenarios.
"""

from __future__ import annotations

import pandas as pd


METRICS = ["accuracy", "precision", "recall", "f1", "auc"]


def build_summary(per_split_df: pd.DataFrame) -> pd.DataFrame:
    agg = {m: ["mean", "std"] for m in METRICS}
    summary = per_split_df.groupby("scenario").agg(agg).round(6)
    summary.columns = [f"{a}_{b}" for a, b in summary.columns]
    summary = summary.reset_index()

    split_count = per_split_df.groupby("scenario")["split_num"].count().rename("n_splits").reset_index()
    summary = summary.merge(split_count, on="scenario", how="left")

    summary = summary.sort_values("auc_mean", ascending=False, na_position="last").reset_index(drop=True)
    summary.insert(0, "rank_auc", summary.index + 1)
    return summary


def build_pairwise_comparison(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Create direct delta table (hybrid_adaptive - native_masking)."""
    req = {"hybrid_adaptive", "native_masking"}
    if not req.issubset(set(summary_df["scenario"])):
        return pd.DataFrame()

    left = summary_df.set_index("scenario").loc["hybrid_adaptive"]
    right = summary_df.set_index("scenario").loc["native_masking"]

    rows = []
    for metric in ["accuracy_mean", "precision_mean", "recall_mean", "f1_mean", "auc_mean"]:
        rows.append(
            {
                "metric": metric,
                "hybrid_adaptive": left.get(metric),
                "native_masking": right.get(metric),
                "delta_hybrid_minus_native": left.get(metric) - right.get(metric),
            }
        )

    return pd.DataFrame(rows)
