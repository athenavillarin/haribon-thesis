"""
ensemble_evaluate.py
====================
Metric computation and comparison table generation for the ensemble pipeline.

Produces:
  ensemble_per_split_metrics.csv   — AUC, F1, Precision, Recall, Accuracy
                                     for every model & strategy × every split
  ensemble_summary.csv             — mean ± std across splits, ranked by AUC
  obj2_model_comparison_final.csv  — final Obj 2 comparison:
                                     LSTM | GRU | Transformer | XGBoost | Best Ensemble
  ensemble_comparison_auc_mean.png — bar chart showing ensemble boost vs individual models (AUC)
  ensemble_comparison_f1_mean.png  — bar chart showing ensemble boost vs individual models (F1)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent.parent

# Paths to existing per-model metrics (used to compile Obj 2 comparison)
LSTM_METRICS_CSV        = _ROOT / "lstm"              / "saved_model" / "rolling_origin_metrics.csv"
GRU_METRICS_CSV         = _ROOT / "gru"               / "saved_model" / "rolling_origin_metrics.csv"
TRANSFORMER_METRICS_CSV = _ROOT / "transformer_model" / "results"      / "transformer_summary.csv"
XGBOOST_SPLIT_METRICS_CSV = _ROOT / "xgboost_model"   / "results"      / "xgboost_split_metrics.csv"
TASK4_SUMMARY_CSV        = _ROOT / "task_4"          / "task4_results" / "xgboost_results_summary.csv"


# ---------------------------------------------------------------------------
# Core metric computation
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """Compute standard binary classification metrics from probabilities."""
    if len(y_true) == 0 or np.all(np.isnan(y_prob)):
        return dict(accuracy=np.nan, precision=np.nan, recall=np.nan, f1=np.nan, auc=np.nan)

    y_prob_clean = np.where(np.isnan(y_prob), 0.5, y_prob)
    y_pred = (y_prob_clean >= threshold).astype(int)

    metrics = {
        "accuracy":  float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall":    float(recall_score(y_true, y_pred, zero_division=0)),
        "f1":        float(f1_score(y_true, y_pred, zero_division=0)),
    }

    if len(np.unique(y_true)) < 2:
        metrics["auc"] = np.nan
    else:
        try:
            metrics["auc"] = float(roc_auc_score(y_true, y_prob_clean))
        except Exception:
            metrics["auc"] = np.nan

    return metrics


# ---------------------------------------------------------------------------
# Per-split results builder
# ---------------------------------------------------------------------------

def build_per_split_records(
    split_results: List[Dict],
) -> pd.DataFrame:
    """
    Flatten the per-split evaluation results into a DataFrame.

    split_results is a list of dicts, each with keys:
      split_num, train_end, test_start, test_end,
      n_train, n_test, positive_rate,
      model_probs: {model_name: probs array},
      strategy_probs: {strategy_name: probs array},
      y_test: ground truth
    """
    rows = []
    for sr in split_results:
        y_test = sr["y_test"]
        base = dict(
            split_num       = sr["split_num"],
            train_end       = sr["train_end"],
            test_start      = sr["test_start"],
            test_end        = sr["test_end"],
            n_train         = sr["n_train"],
            n_test          = sr["n_test"],
            positive_rate   = float(np.mean(y_test)) if len(y_test) > 0 else np.nan,
        )

        # Individual model metrics
        for model, probs in sr.get("model_probs", {}).items():
            m = compute_metrics(y_test, probs)
            rows.append({**base, "source": "model", "name": model, **m})

        # Ensemble strategy metrics
        for strategy, probs in sr.get("strategy_probs", {}).items():
            m = compute_metrics(y_test, probs)
            rows.append({**base, "source": "ensemble", "name": strategy, **m})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary(per_split_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-split metrics into mean ± std, ranked by AUC."""
    metric_cols = ["accuracy", "precision", "recall", "f1", "auc"]
    agg = {col: ["mean", "std"] for col in metric_cols}
    summary = per_split_df.groupby(["source", "name"]).agg(agg).round(6)
    summary.columns = [f"{a}_{b}" for a, b in summary.columns]
    summary = summary.reset_index()

    count = per_split_df.groupby(["source", "name"])["split_num"].count().rename("n_splits").reset_index()
    summary = summary.merge(count, on=["source", "name"], how="left")
    summary = summary.sort_values(
        ["auc_mean", "f1_mean", "recall_mean"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    summary.insert(0, "rank_auc", range(1, len(summary) + 1))
    return summary


# ---------------------------------------------------------------------------
# Objective 2 final model comparison table
# ---------------------------------------------------------------------------

def _load_rnn_metrics(csv_path: Path, model_name: str) -> Optional[Dict]:
    """
    Load LSTM or GRU rolling-origin metrics CSV and compute mean ± std.
    Columns: split, train_end, test_years, threshold, accuracy, precision,
             recall, f1_macro, f1_weighted, auc_roc
    """
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    # Use all available splits
    return {
        "model": model_name,
        "auc_mean":       round(df["auc_roc"].mean(),          4),
        "auc_std":        round(df["auc_roc"].std(),           4),
        "accuracy_mean":  round(df["accuracy"].mean(),         4),
        "accuracy_std":   round(df["accuracy"].std(),          4),
        "precision_mean": round(df["precision"].mean(),        4),
        "precision_std":  round(df["precision"].std(),         4),
        "recall_mean":    round(df["recall"].mean(),           4),
        "recall_std":     round(df["recall"].std(),            4),
        "f1_mean":        round(df["f1_macro"].mean(),         4),
        "f1_std":         round(df["f1_macro"].std(),          4),
        "n_splits":       len(df),
        "notes":          f"Splits 1-{len(df)} of {len(df)} rolling-origin yearly splits",
    }


def _load_transformer_metrics(preferred_scenario: str = "native_masking") -> Optional[Dict]:
    """Load Transformer summary, preferring the requested scenario."""
    if not TRANSFORMER_METRICS_CSV.exists():
        return None
    df = pd.read_csv(TRANSFORMER_METRICS_CSV)
    row = df[df["scenario"] == preferred_scenario]
    if row.empty:
        row = df.sort_values(["auc_mean", "f1_mean", "recall_mean"], ascending=[False, False, False]).iloc[0:1]
    row = row.iloc[0]
    return {
        "model":          "Transformer",
        "auc_mean":       round(float(row.get("auc_mean", np.nan)),       4),
        "auc_std":        round(float(row.get("auc_std",  np.nan)),       4),
        "accuracy_mean":  round(float(row.get("accuracy_mean", np.nan)),  4),
        "accuracy_std":   round(float(row.get("accuracy_std",  np.nan)),  4),
        "precision_mean": round(float(row.get("precision_mean", np.nan)), 4),
        "precision_std":  round(float(row.get("precision_std",  np.nan)), 4),
        "recall_mean":    round(float(row.get("recall_mean", np.nan)),    4),
        "recall_std":     round(float(row.get("recall_std",  np.nan)),    4),
        "f1_mean":        round(float(row.get("f1_mean", np.nan)),        4),
        "f1_std":         round(float(row.get("f1_std",  np.nan)),        4),
        "n_splits":       int(row.get("n_splits", 4)),
        "notes":          f"{row.get('scenario', preferred_scenario)} scenario from transformer_summary.csv",
    }


def _load_xgboost_metrics() -> Optional[Dict]:
    """Load XGBoost downstream evaluation summary, preferring the 6-split notebook output."""
    if XGBOOST_SPLIT_METRICS_CSV.exists():
        df = pd.read_csv(XGBOOST_SPLIT_METRICS_CSV)
        return {
            "model":          "XGBoost (Hybrid: Gap-Type Adaptive)",
            "auc_mean":       round(df["auc"].mean(), 4),
            "auc_std":        round(df["auc"].std(), 4),
            "accuracy_mean":  round(df["accuracy"].mean(), 4),
            "accuracy_std":   round(df["accuracy"].std(), 4),
            "precision_mean": round(df["precision"].mean(), 4),
            "precision_std":  round(df["precision"].std(), 4),
            "recall_mean":    round(df["recall"].mean(), 4),
            "recall_std":     round(df["recall"].std(), 4),
            "f1_mean":        round(df["f1"].mean(), 4),
            "f1_std":         round(df["f1"].std(), 4),
            "n_splits":       int(df["split"].nunique()),
            "notes":          "Hybrid-adaptive XGBoost notebook evaluation across 6 temporal splits",
        }

    if not TASK4_SUMMARY_CSV.exists():
        return None
    df = pd.read_csv(TASK4_SUMMARY_CSV)
    # Best method by AUC
    best = df.sort_values("auc_mean", ascending=False).iloc[0]
    return {
        "model":          f"XGBoost ({best.get('method_name', 'best method')})",
        "auc_mean":       round(float(best.get("auc_mean", np.nan)), 4),
        "auc_std":        round(float(best.get("auc_std",  np.nan)), 4),
        "accuracy_mean":  np.nan,
        "accuracy_std":   np.nan,
        "precision_mean": np.nan,
        "precision_std":  np.nan,
        "recall_mean":    np.nan,
        "recall_std":     np.nan,
        "f1_mean":        round(float(best.get("f1_mean", np.nan)), 4),
        "f1_std":         round(float(best.get("f1_std",  np.nan)), 4),
        "n_splits":       int(best.get("n_splits", 4)),
        "notes":          "Task 4 downstream XGBoost evaluation (fallback source)",
    }


def build_obj2_comparison(
    ensemble_summary: pd.DataFrame,
    output_path: Optional[Path] = None,
    transformer_scenario: str = "native_masking",
) -> pd.DataFrame:
    """
    Compile the full Objective 2 model comparison table.

    Rows: LSTM, GRU, Transformer, XGBoost, Best Ensemble (from ensemble_summary)
    Columns: model, auc_mean, auc_std, accuracy_mean, f1_mean, f1_std, n_splits, notes

    Also appends the best ensemble strategy row.
    """
    records = []

    lstm_row = _load_rnn_metrics(LSTM_METRICS_CSV, "LSTM")
    gru_row  = _load_rnn_metrics(GRU_METRICS_CSV,  "GRU")
    trans_row = _load_transformer_metrics(preferred_scenario=transformer_scenario)
    xgb_row  = _load_xgboost_metrics()

    for row in [lstm_row, gru_row, trans_row, xgb_row]:
        if row is not None:
            records.append(row)

    # Best ensemble strategy from ensemble_summary
    ens_rows = ensemble_summary[ensemble_summary["source"] == "ensemble"]
    if not ens_rows.empty:
        best_ens = ens_rows.sort_values(
            ["auc_mean", "f1_mean", "recall_mean"],
            ascending=[False, False, False],
            na_position="last",
        ).iloc[0]
        records.append({
            "model":          f"Ensemble ({best_ens['name']})",
            "auc_mean":       round(float(best_ens.get("auc_mean", np.nan)), 4),
            "auc_std":        round(float(best_ens.get("auc_std",  np.nan)), 4),
            "accuracy_mean":  round(float(best_ens.get("accuracy_mean", np.nan)), 4),
            "accuracy_std":   round(float(best_ens.get("accuracy_std",  np.nan)), 4),
            "precision_mean": round(float(best_ens.get("precision_mean", np.nan)), 4),
            "precision_std":  round(float(best_ens.get("precision_std",  np.nan)), 4),
            "recall_mean":    round(float(best_ens.get("recall_mean", np.nan)), 4),
            "recall_std":     round(float(best_ens.get("recall_std",  np.nan)), 4),
            "f1_mean":        round(float(best_ens.get("f1_mean", np.nan)), 4),
            "f1_std":         round(float(best_ens.get("f1_std",  np.nan)), 4),
            "n_splits":       int(best_ens.get("n_splits", 4)),
            "notes":          "Best ensemble strategy by AUC, then F1, then Recall across 6 common splits",
        })

    df = pd.DataFrame(records)
    df = df.sort_values(
        ["auc_mean", "f1_mean", "recall_mean"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def print_summary_table(summary: pd.DataFrame) -> None:
    cols = ["rank_auc", "source", "name", "accuracy_mean", "precision_mean",
            "recall_mean", "f1_mean", "auc_mean", "n_splits"]
    printable = summary[[c for c in cols if c in summary.columns]]
    print(printable.to_string(index=False))


def print_obj2_comparison(df: pd.DataFrame) -> None:
    cols = ["rank", "model", "auc_mean", "auc_std", "f1_mean", "f1_std",
            "accuracy_mean", "n_splits", "notes"]
    printable = df[[c for c in cols if c in df.columns]]
    print(printable.to_string(index=False))


# ---------------------------------------------------------------------------  
# Plotting functions
# ---------------------------------------------------------------------------

def plot_ensemble_comparison(
    summary_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    metric: str = "auc_mean",
) -> None:
    """
    Generate a bar chart comparing individual base models vs ensemble strategies.
    
    Shows the "Ensemble Boost" by comparing mean AUC or F1-score across splits.
    
    Parameters:
    - summary_df: DataFrame from build_summary() with model/ensemble rows
    - output_path: Where to save the PNG (default: results/ensemble_comparison_{metric}.png)
    - metric: Which metric to plot ('auc_mean' or 'f1_mean')
    """
    if output_path is None:
        output_path = _ROOT / "ensemble_model" / "results" / f"ensemble_comparison_{metric}.png"
    
    # Separate individual models and ensembles
    individual = summary_df[summary_df["source"] == "model"].copy()
    ensembles = summary_df[summary_df["source"] == "ensemble"].copy()
    
    # Combine for plotting
    plot_data = pd.concat([
        individual.assign(category="Individual Models"),
        ensembles.assign(category="Ensemble Strategies")
    ])
    
    # Sort by metric descending
    plot_data = plot_data.sort_values(metric, ascending=False)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Color scheme: blue for individuals, green for ensembles
    colors = ["skyblue" if cat == "Individual Models" else "lightgreen" 
              for cat in plot_data["category"]]
    
    bars = ax.bar(
        plot_data["name"], 
        plot_data[metric], 
        color=colors,
        edgecolor="black",
        alpha=0.8
    )
    
    # Add value labels on bars
    for bar, value in zip(bars, plot_data[metric]):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.01,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )
    
    # Formatting
    metric_label = "AUC-ROC" if metric == "auc_mean" else "F1-Score"
    ax.set_title(f"Model Performance Comparison: {metric_label} Across 6 Splits\nEnsemble Boost Demonstration", 
                 fontsize=14, fontweight="bold", pad=20)
    ax.set_ylabel(f"Mean {metric_label}", fontsize=12)
    ax.set_xlabel("Models/Strategies", fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    
    # Rotate x labels for readability
    plt.xticks(rotation=45, ha="right")
    
    # Legend
    handles = [
        plt.Rectangle((0,0),1,1, color="skyblue", alpha=0.8),
        plt.Rectangle((0,0),1,1, color="lightgreen", alpha=0.8)
    ]
    ax.legend(handles, ["Individual Models", "Ensemble Strategies"], 
              loc="upper right", fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved ensemble comparison chart to: {output_path}")
    
    plt.close()
