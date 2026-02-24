"""Generate Task 5 thesis deliverables from Tasks 2–4 outputs.

Creates:
  - task_5/results/master_comparison_table.csv
  - task_5/results/best_method_per_gap.csv
  - task_5/results/per_split_auc.csv
  - task_5/results/warnings.txt
  - task_5/figures/fig1_rmse_mae_comparison.png
  - task_5/figures/fig2_r2_heatmap.png
  - task_5/figures/fig3_performance_decay.png
  - task_5/figures/fig4_xgboost_auc_f1.png
  - task_5/figures/fig5_rolling_origin_splits.png
  - task_5/figures/fig6_shap_features.png

Rules:
  - No placeholders: values come only from existing CSV outputs.
  - Missing values are written as NaN and explicitly logged in warnings.txt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns


@dataclass(frozen=True)
class Paths:
    root: Path
    task5_dir: Path
    results_dir: Path
    figures_dir: Path

    t2_summary: Path
    t2_bygap: Path

    t3_summary: Path
    t3_detail: Path

    t4_summary: Path
    t4_per_split: Path
    t4_shap_dir: Path


def build_paths() -> Paths:
    task5_dir = Path(__file__).resolve().parents[1]
    root = task5_dir.parents[0]
    return Paths(
        root=root,
        task5_dir=task5_dir,
        results_dir=task5_dir / "results",
        figures_dir=task5_dir / "figures",
        t2_summary=root / "task_2" / "task2_results" / "summary_table.csv",
        t2_bygap=root / "task_2" / "task2_results" / "method_comparison_metrics.csv",
        t3_summary=root / "task_3" / "task3_results" / "summary_table.csv",
        t3_detail=root / "task_3" / "task3_results" / "spatial_imputation_results.csv",
        t4_summary=root / "task_4" / "task4_results" / "xgboost_results_summary.csv",
        t4_per_split=root / "task_4" / "task4_results" / "xgboost_results_per_split.csv",
        t4_shap_dir=root / "task_4" / "task4_results" / "shap_importance",
    )


def normalize_method_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    normalized = name.replace("→", "->")
    if normalized.strip() == "Cross-Location Regression":
        return "Cross-Location Linear Regression"
    return normalized


def method_metadata() -> pd.DataFrame:
    rows = [
        # Task 2 (Temporal)
        ("Linear Interpolation", "Task 2", "Temporal"),
        ("Climatological Substitution", "Task 2", "Temporal"),
        # Task 3 (Spatial + Hybrid)
        ("Spatial Kriging", "Task 3", "Spatial"),
        ("Cross-Location Linear Regression", "Task 3", "Spatial"),
        ("Cross-Location KNN", "Task 3", "Spatial"),
        ("Distance-Weighted Average", "Task 3", "Spatial"),
        ("Advection-Based", "Task 3", "Spatial"),
        ("EOF/PCA Spatial Modes", "Task 3", "Spatial"),
        ("Hybrid: Sequential Temporal->Spatial", "Task 3", "Hybrid"),
        ("Hybrid: Gap-Type Adaptive", "Task 3", "Hybrid"),
        ("Hybrid: Temporal-Spatial Ensemble", "Task 3", "Hybrid"),
    ]
    return pd.DataFrame(rows, columns=["Method", "Task", "Type"])


def safe_read_csv(path: Path, warnings: list[str], **kwargs) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, **kwargs)
    except FileNotFoundError:
        warnings.append(f"Missing input file: {path}")
        return None


def write_warnings(path: Path, warnings: Iterable[str]) -> None:
    lines = ["Task 5 warnings / missing-data log", ""]
    for msg in warnings:
        lines.append(f"- {msg}")
    path.write_text("\n".join(lines), encoding="utf-8")


def compute_master_comparison_table(
    meta: pd.DataFrame,
    t2_summary: pd.DataFrame | None,
    t3_summary: pd.DataFrame | None,
    t4_summary: pd.DataFrame | None,
    warnings: list[str],
) -> pd.DataFrame:
    # ---- imputation metrics (Tasks 2 & 3) ----
    imp_rows: list[pd.DataFrame] = []
    if t2_summary is not None:
        t2 = t2_summary.copy()
        if "method_name" in t2.columns:
            t2 = t2.rename(
                columns={
                    "method_name": "Method",
                    "rmse_mean": "Imputation RMSE",
                    "mae_mean": "Imputation MAE",
                    "r2_mean": "Imputation R²",
                }
            )[["Method", "Imputation RMSE", "Imputation MAE", "Imputation R²"]]
            imp_rows.append(t2)
    if t3_summary is not None:
        t3 = t3_summary.copy()
        if "method_name" in t3.columns:
            t3 = t3.rename(
                columns={
                    "method_name": "Method",
                    "rmse": "Imputation RMSE",
                    "mae": "Imputation MAE",
                    "r2": "Imputation R²",
                }
            )[["Method", "Imputation RMSE", "Imputation MAE", "Imputation R²"]]
            imp_rows.append(t3)

    if imp_rows:
        imputation = pd.concat(imp_rows, ignore_index=True)
        imputation["Method"] = imputation["Method"].map(normalize_method_name)
        imputation = imputation.drop_duplicates(subset=["Method"], keep="first")
    else:
        imputation = pd.DataFrame(
            columns=["Method", "Imputation RMSE", "Imputation MAE", "Imputation R²"]
        )
        warnings.append("No imputation summary tables could be loaded; imputation metrics will be NaN.")

    # ---- downstream metrics (Task 4) ----
    if t4_summary is not None:
        downstream = t4_summary.copy()
        downstream["method_name"] = downstream["method_name"].map(normalize_method_name)
        downstream = downstream.rename(
            columns={
                "method_name": "Method",
                "rmse_mean": "XGBoost RMSE",
                "mae_mean": "XGBoost MAE",
                "r2_mean": "XGBoost R²",
                "f1_mean": "XGBoost F1",
                "auc_mean": "XGBoost AUC",
            }
        )[["Method", "XGBoost RMSE", "XGBoost MAE", "XGBoost R²", "XGBoost F1", "XGBoost AUC"]]
    else:
        downstream = pd.DataFrame(
            columns=["Method", "XGBoost RMSE", "XGBoost MAE", "XGBoost R²", "XGBoost F1", "XGBoost AUC"]
        )
        warnings.append("No Task 4 summary table could be loaded; XGBoost metrics will be NaN.")

    # ---- join ----
    df = meta.merge(imputation, on="Method", how="left").merge(downstream, on="Method", how="left")

    # ---- explicit missing-data warnings ----
    for _, row in df.iterrows():
        method = row["Method"]
        if pd.isna(row.get("Imputation RMSE")):
            warnings.append(f"Missing imputation metrics for method: {method}")
        if pd.isna(row.get("XGBoost AUC")):
            warnings.append(f"Missing XGBoost metrics for method: {method}")

    # ---- AUC rank (descending; keep missing as NaN) ----
    df["AUC Rank"] = df["XGBoost AUC"].rank(method="min", ascending=False, na_option="keep").astype("Int64")

    # Column order required by spec
    df = df[
        [
            "Method",
            "Task",
            "Type",
            "Imputation RMSE",
            "Imputation MAE",
            "Imputation R²",
            "XGBoost RMSE",
            "XGBoost MAE",
            "XGBoost R²",
            "XGBoost F1",
            "XGBoost AUC",
            "AUC Rank",
        ]
    ]

    # Sort for readability: AUC Rank then Method
    df = df.sort_values(by=["AUC Rank", "Method"], ascending=[True, True], na_position="last").reset_index(drop=True)
    return df


def compute_best_method_per_gap(
    t2_bygap: pd.DataFrame | None,
    t3_detail: pd.DataFrame | None,
    warnings: list[str],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    if t2_bygap is not None:
        t2 = t2_bygap.rename(
            columns={
                "mask_type": "Gap Pattern",
                "method_name": "Method",
                "rmse_mean": "RMSE",
                "mae_mean": "MAE",
                "r2_mean": "R²",
            }
        )[["Gap Pattern", "Method", "RMSE", "MAE", "R²"]].copy()
        t2["Source"] = "Task 2"
        t2["Method"] = t2["Method"].map(normalize_method_name)
        frames.append(t2)
    else:
        warnings.append("Task 2 by-gap metrics missing; gap-pattern comparison may be incomplete.")

    if t3_detail is not None:
        detail = t3_detail.copy()
        detail["method_name"] = detail["method_name"].map(normalize_method_name)
        agg = (
            detail.groupby(["mask_type", "method_name"], dropna=False)[["rmse", "mae", "r2"]]
            .mean(numeric_only=True)
            .reset_index()
            .rename(
                columns={
                    "mask_type": "Gap Pattern",
                    "method_name": "Method",
                    "rmse": "RMSE",
                    "mae": "MAE",
                    "r2": "R²",
                }
            )
        )
        agg["Source"] = "Task 3"
        frames.append(agg)
    else:
        warnings.append("Task 3 detailed results missing; gap-pattern comparison may be incomplete.")

    if not frames:
        return pd.DataFrame(columns=["Gap Pattern", "Best Method", "RMSE", "MAE", "R²", "Source"])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["Gap Pattern"]).copy()

    # Choose lowest RMSE per gap pattern
    best_rows: list[dict] = []
    for gap, sub in combined.groupby("Gap Pattern", dropna=False):
        sub = sub.dropna(subset=["RMSE"]).sort_values("RMSE", ascending=True)
        if sub.empty:
            warnings.append(f"No RMSE values available to choose best method for gap: {gap}")
            best_rows.append(
                {
                    "Gap Pattern": gap,
                    "Best Method": np.nan,
                    "RMSE": np.nan,
                    "MAE": np.nan,
                    "R²": np.nan,
                    "Source": np.nan,
                }
            )
            continue
        best = sub.iloc[0]
        best_rows.append(
            {
                "Gap Pattern": gap,
                "Best Method": best["Method"],
                "RMSE": best["RMSE"],
                "MAE": best["MAE"],
                "R²": best["R²"],
                "Source": best["Source"],
            }
        )

    best_df = pd.DataFrame(best_rows)
    order = [
        "block_7day",
        "block_14day",
        "random_10",
        "random_20",
        "seasonal",
        "cross_variable",
        "rolling_origin",
        "rolling_origin_180",
    ]
    best_df["_order"] = best_df["Gap Pattern"].apply(lambda x: order.index(x) if x in order else 999)
    best_df = best_df.sort_values(["_order", "Gap Pattern"], ascending=[True, True]).drop(columns=["_order"])
    return best_df[["Gap Pattern", "Best Method", "RMSE", "MAE", "R²", "Source"]]


def compute_per_split_auc(t4_per_split: pd.DataFrame | None, warnings: list[str]) -> pd.DataFrame:
    if t4_per_split is None:
        warnings.append("Task 4 per-split results missing; per_split_auc.csv not generated.")
        return pd.DataFrame(columns=["method_name", "split_num", "auc", "note"])

    df = t4_per_split.copy()
    df["method_name"] = df["method_name"].map(normalize_method_name)
    out = df[["method_name", "split_num", "auc"]].copy()
    out["note"] = ""
    out.loc[out["split_num"] == 3, "note"] = "Split 3 AUC may be uninformative (very low/zero bloom-event prevalence)."
    return out.sort_values(["method_name", "split_num"], ascending=[True, True]).reset_index(drop=True)


def plot_fig1_rmse_mae(master: pd.DataFrame, out_path: Path) -> None:
    type_color = {"Temporal": "#4C9BE8", "Spatial": "#F28C28", "Hybrid": "#5CB85C"}

    df = master.dropna(subset=["Imputation RMSE"]).copy()
    # Exclude unstable ensemble outlier
    df = df[df["Method"] != "Hybrid: Temporal-Spatial Ensemble"].copy()
    df = df.sort_values("Imputation RMSE", ascending=True)

    x = np.arange(len(df))
    w = 0.38
    colors = [type_color.get(t, "#999999") for t in df["Type"]]

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(14, 5.5))
    b1 = ax.bar(
        x - w / 2,
        df["Imputation RMSE"],
        w,
        color=colors,
        alpha=0.9,
        edgecolor="white",
        linewidth=0.6,
        label="RMSE",
    )
    b2 = ax.bar(
        x + w / 2,
        df["Imputation MAE"],
        w,
        color=colors,
        alpha=0.5,
        edgecolor="white",
        linewidth=0.6,
        hatch="//",
        label="MAE",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [str(m).replace(": ", ":\n").replace("->", "->\n") for m in df["Method"]],
        rotation=25,
        ha="right",
        fontsize=8.5,
    )
    ax.set_ylabel("Error (lower = better)", fontsize=10)
    ax.set_title(
        "Figure 1 — Imputation RMSE & MAE Across Methods\n"
        "(Tasks 2 & 3; sorted by RMSE; Hybrid: Temporal-Spatial Ensemble excluded as outlier)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylim(0, float(df["Imputation RMSE"].max()) * 1.2)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.grid(axis="y", alpha=0.3)

    for b, v in zip(b1, df["Imputation RMSE"]):
        ax.text(b.get_x() + b.get_width() / 2, float(v) + 0.01, f"{float(v):.3f}", ha="center", va="bottom", fontsize=7)
    for b, v in zip(b2, df["Imputation MAE"]):
        ax.text(b.get_x() + b.get_width() / 2, float(v) + 0.01, f"{float(v):.3f}", ha="center", va="bottom", fontsize=7)

    legend_type = [mpatches.Patch(facecolor=c, label=t) for t, c in type_color.items()]
    legend_metric = [
        mpatches.Patch(facecolor="grey", alpha=0.9, label="RMSE (solid)"),
        mpatches.Patch(facecolor="grey", alpha=0.5, hatch="//", label="MAE (hatched)"),
    ]
    ax.legend(
        handles=legend_type + legend_metric,
        fontsize=8.5,
        ncol=5,
        loc="upper left",
        framealpha=0.8,
    )

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig2_r2_heatmap(t2_bygap: pd.DataFrame | None, t3_detail: pd.DataFrame | None, out_path: Path) -> None:
    gap_pretty = {
        "block_14day": "Block 14-day",
        "block_7day": "Block 7-day",
        "cross_variable": "Cross-Variable",
        "random_10": "Random 10%",
        "random_20": "Random 20%",
        "rolling_origin": "Rolling Origin",
        "rolling_origin_180": "Rolling 180d",
        "seasonal": "Seasonal",
    }
    frames: list[pd.DataFrame] = []

    if t2_bygap is not None:
        t2 = t2_bygap[["method_name", "mask_type", "r2_mean"]].copy()
        t2["method_name"] = t2["method_name"].map(normalize_method_name)
        t2 = t2.rename(columns={"method_name": "Method", "mask_type": "Gap Pattern", "r2_mean": "R²"})
        frames.append(t2)
    if t3_detail is not None:
        t3 = (
            t3_detail.groupby(["method_name", "mask_type"], dropna=False)["r2"]
            .mean(numeric_only=True)
            .reset_index()
        )
        t3["method_name"] = t3["method_name"].map(normalize_method_name)
        t3 = t3.rename(columns={"method_name": "Method", "mask_type": "Gap Pattern", "r2": "R²"})
        frames.append(t3)

    combined = pd.concat(frames, ignore_index=True)
    pivot = combined.pivot_table(index="Method", columns="Gap Pattern", values="R²", aggfunc="mean")

    # Only keep the known gap patterns and make them readable
    gap_order = [
        "block_7day",
        "block_14day",
        "random_10",
        "random_20",
        "seasonal",
        "cross_variable",
        "rolling_origin",
        "rolling_origin_180",
    ]
    cols_present = [c for c in gap_order if c in pivot.columns]
    pivot = pivot.reindex(columns=cols_present)
    pivot.columns = [gap_pretty.get(c, c) for c in pivot.columns]

    # Clip extreme negatives for colour scale; annotate true values
    pivot_clipped = pivot.clip(lower=-1.5, upper=1.0)
    annot_vals = pivot.round(2).astype(object)
    annot_vals = annot_vals.where(~pivot.isna(), "")

    sns.set_style("white")
    fig, ax = plt.subplots(figsize=(13, 5))
    sns.heatmap(
        pivot_clipped,
        ax=ax,
        annot=annot_vals,
        fmt="",
        cmap="RdYlGn",
        vmin=-1.5,
        vmax=1.0,
        linewidths=0.5,
        linecolor="white",
        annot_kws={"size": 8},
        cbar_kws={"label": "R² (colour clipped to [−1.5, 1])"},
    )
    ax.set_title(
        "Figure 2 — R² by Method × Gap Pattern\n"
        "Annotated with true R²; colour scale clipped at −1.5 for readability",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=30, labelsize=9)
    ax.tick_params(axis="y", rotation=0, labelsize=8.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig3_performance_decay(best_per_gap: pd.DataFrame, out_path: Path) -> None:
    # Legacy plot kept for backwards-compatibility (not used by Task 5 main pipeline).
    df = best_per_gap.copy()
    df = df.dropna(subset=["RMSE"]).copy()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["Gap Pattern"], df["RMSE"], marker="o")
    ax.set_title("Figure 3 (legacy) — Best RMSE per Gap Pattern")
    ax.set_xlabel("Gap Pattern")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig3_decay_curve(
    t2_bygap: pd.DataFrame | None,
    t3_detail: pd.DataFrame | None,
    out_path: Path,
) -> None:
    gap_length_map = {
        "random_10": 1,
        "random_20": 2,
        "block_7day": 7,
        "block_14day": 14,
        "seasonal": 30,
        "rolling_origin": 90,
        "rolling_origin_180": 180,
    }
    decay_methods = [
        "Linear Interpolation",
        "Climatological Substitution",
        "Cross-Location Linear Regression",
        "Spatial Kriging",
        "Hybrid: Gap-Type Adaptive",
    ]

    frames: list[pd.DataFrame] = []
    if t2_bygap is not None:
        t2 = t2_bygap.rename(
            columns={
                "mask_type": "gap_pattern",
                "method_name": "method_name",
                "rmse_mean": "rmse",
            }
        )[["gap_pattern", "method_name", "rmse"]].copy()
        t2["method_name"] = t2["method_name"].map(normalize_method_name)
        frames.append(t2)
    if t3_detail is not None:
        t3 = (
            t3_detail.groupby(["mask_type", "method_name"], dropna=False)["rmse"]
            .mean(numeric_only=True)
            .reset_index()
            .rename(columns={"mask_type": "gap_pattern"})
        )
        t3["method_name"] = t3["method_name"].map(normalize_method_name)
        frames.append(t3)

    all_bygap = pd.concat(frames, ignore_index=True)
    decay_df = all_bygap[
        all_bygap["method_name"].isin(decay_methods)
        & all_bygap["gap_pattern"].isin(gap_length_map)
    ].copy()
    decay_df["gap_days"] = decay_df["gap_pattern"].map(gap_length_map)

    decay_rmse = decay_df.pivot_table(index="gap_days", columns="method_name", values="rmse", aggfunc="mean")

    method_style = {
        "Linear Interpolation": ("#4C9BE8", "-", "o"),
        "Climatological Substitution": ("#E84C4C", "--", "s"),
        "Cross-Location Linear Regression": ("#F28C28", "-.", "D"),
        "Spatial Kriging": ("#9B59B6", "-", "^"),
        "Hybrid: Gap-Type Adaptive": ("#5CB85C", "-", "P"),
    }

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    for method, (col, ls, mk) in method_style.items():
        if method not in decay_rmse.columns:
            continue
        y = decay_rmse[method].dropna()
        ax.plot(
            y.index,
            y.values,
            color=col,
            linestyle=ls,
            marker=mk,
            linewidth=2.2,
            markersize=8,
            label=method,
        )

    ax.axvline(
        14,
        color="red",
        linestyle=":",
        linewidth=1.5,
        alpha=0.7,
        label="14-day threshold\n(temporal methods break down)",
    )
    ax.set_xlabel("Approximate Gap Length (days)", fontsize=10)
    ax.set_ylabel("RMSE (mean, across all variables)", fontsize=10)
    ax.set_title(
        "Figure 3 — Performance Decay Curve by Gap Length\n"
        "RMSE as gap length increases; red dotted line = 14-day threshold",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xticks(sorted(gap_length_map.values()))
    ax.set_xticklabels([f"{d}d" for d in sorted(gap_length_map.values())], fontsize=9)
    ax.legend(fontsize=8.5, loc="upper left", framealpha=0.85)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig4_xgboost_auc_f1(master: pd.DataFrame, out_path: Path) -> None:
    type_color = {"Temporal": "#4C9BE8", "Spatial": "#F28C28", "Hybrid": "#5CB85C"}

    df = master.dropna(subset=["XGBoost AUC"]).copy()
    df = df.sort_values("XGBoost AUC", ascending=False)

    x = np.arange(len(df))
    colors = [type_color.get(t, "#999999") for t in df["Type"]]
    labels = [
        str(m).replace(": ", ":\n").replace("->", "->\n")
        for m in df["Method"]
    ]

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # Left: AUC
    ax = axes[0]
    bars = ax.bar(x, df["XGBoost AUC"], color=colors, edgecolor="white", linewidth=0.7)
    ax.axhline(
        0.5,
        color="red",
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label="Random baseline (AUC=0.5)",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("AUC-ROC")
    ax.set_ylim(0, 0.85)
    ax.set_title("XGBoost AUC-ROC\n↑ higher = better bloom discrimination", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, df["XGBoost AUC"]):
        ax.text(b.get_x() + b.get_width() / 2, float(v) + 0.008, f"{float(v):.3f}", ha="center", va="bottom", fontsize=7.5)

    # Right: F1
    ax = axes[1]
    f1_vals = df["XGBoost F1"].fillna(0)
    bars = ax.bar(x, f1_vals, color=colors, edgecolor="white", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("F1-Score")
    ax.set_ylim(0, 0.55)
    ax.set_title(
        "XGBoost F1-Score (Bloom Detection)\n↑ higher = better; 0 = no positive predictions made",
        fontsize=10,
        fontweight="bold",
    )
    ax.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, f1_vals):
        if float(v) > 0:
            ax.text(b.get_x() + b.get_width() / 2, float(v) + 0.005, f"{float(v):.3f}", ha="center", va="bottom", fontsize=7.5)

    # Shared legend
    import matplotlib.patches as mpatches

    legend_els = [mpatches.Patch(facecolor=c, label=t) for t, c in type_color.items()]
    fig.legend(handles=legend_els, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04), fontsize=9)
    fig.suptitle("Figure 4 — XGBoost Downstream Bloom Detection Performance (Task 4)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig5_rolling_origin_splits(per_split_auc: pd.DataFrame, out_path: Path) -> None:
    # Legacy plot kept for backwards-compatibility (not used by Task 5 main pipeline).
    df = per_split_auc.copy()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))

    for method, sub in df.groupby("method_name"):
        ax.plot(sub["split_num"], sub["auc"], marker="o", linewidth=1.5, label=method)

    ax.axvspan(2.7, 3.3, color="gray", alpha=0.15)
    ax.text(3, 0.02, "Split 3\n(AUC may be uninformative)", ha="center", va="bottom", fontsize=9)
    ax.set_title("Figure 5 (legacy) — Rolling-Origin Split AUC by Method")
    ax.set_xlabel("Split")
    ax.set_ylabel("AUC")
    ax.set_xticks(sorted(df["split_num"].dropna().unique()))
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig5_auc_f1_per_split(t4_per_split: pd.DataFrame | None, out_path: Path) -> None:
    if t4_per_split is None or t4_per_split.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No Task 4 per-split data available", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    df = t4_per_split.copy()
    df["method_name"] = df["method_name"].map(normalize_method_name)
    df["split_num"] = pd.to_numeric(df["split_num"], errors="coerce")
    df["auc"] = pd.to_numeric(df["auc"], errors="coerce")
    df["f1"] = pd.to_numeric(df["f1"], errors="coerce")
    df["n_train"] = pd.to_numeric(df["n_train"], errors="coerce")

    split_methods = [
        "Linear Interpolation",
        "Climatological Substitution",
        "Hybrid: Gap-Type Adaptive",
        "Hybrid: Sequential Temporal->Spatial",
        "Advection-Based",
    ]
    split_style = {
        "Linear Interpolation": ("#4C9BE8", "-", "o"),
        "Climatological Substitution": ("#E84C4C", "--", "s"),
        "Hybrid: Gap-Type Adaptive": ("#5CB85C", "-", "P"),
        "Hybrid: Sequential Temporal->Spatial": ("#228B22", "-.", "D"),
        "Advection-Based": ("#F28C28", ":", "^"),
    }

    # Build split labels using n_train from the LI method (always present)
    split_labels = []
    for s in [1, 2, 3, 4]:
        n = (
            df[(df["method_name"] == "Linear Interpolation") & (df["split_num"] == s)]["n_train"]
            .dropna()
            .head(1)
        )
        n_val = int(n.iloc[0]) if not n.empty else None
        split_labels.append(f"Split {s}\n(n={n_val})" if n_val is not None else f"Split {s}")

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Figure 5 — XGBoost Performance Across Rolling-Origin Splits\n"
        "(Each split adds ~219 training samples; test window = 90 days)",
        fontsize=11,
        fontweight="bold",
    )

    for (metric, ylabel, title, ylim), ax in zip(
        [
            ("auc", "AUC-ROC", "AUC-ROC (↑ bloom discrimination)", (0, 1.05)),
            ("f1", "F1-Score", "F1-Score (↑ bloom detection)", (0, 0.65)),
        ],
        axes,
    ):
        for m in split_methods:
            if m not in split_style:
                continue
            col, ls, mk = split_style[m]
            sub = df[df["method_name"] == m].sort_values("split_num")
            if sub.empty:
                continue
            ax.plot(
                sub["split_num"],
                sub[metric],
                color=col,
                linestyle=ls,
                marker=mk,
                linewidth=2.2,
                markersize=8,
                label=m,
            )
        if metric == "auc":
            ax.axhline(0.5, color="gray", linestyle=":", linewidth=1, alpha=0.6, label="Random (0.5)")
        ax.set_xticks([1, 2, 3, 4])
        ax.set_xticklabels(split_labels, fontsize=8.5)
        ax.set_xlabel("Rolling-Origin Split →")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)
        ax.set_ylim(*ylim)
        ax.grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.12), fontsize=8.5)

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fig6_shap_features(shap_dir: Path, out_path: Path) -> bool:
    shap_paths = sorted(shap_dir.glob("shap_*.csv"))
    if not shap_paths:
        return False

    shap_frames: list[pd.DataFrame] = []
    for p in shap_paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "method" not in df.columns:
            # infer from filename
            df = df.copy()
            df["method"] = p.stem.replace("shap_", "")
        shap_frames.append(df)

    if not shap_frames:
        return False

    shap_all = pd.concat(shap_frames, ignore_index=True)

    method_pretty = {
        "linear_interpolation": "Linear Interp.",
        "climatological": "Climatological",
        "cross_location_knn": "XLoc KNN",
        "cross_location_regression": "XLoc Regression",
        "distance_weighted": "Distance-Weighted",
        "eof_pca": "EOF/PCA",
        "hybrid_adaptive": "Hybrid Adaptive",
        "hybrid_sequential": "Hybrid Sequential",
        "advection": "Advection-Based",
    }

    methods_shap = sorted([m for m in shap_all["method"].dropna().unique()])
    ncols = 3
    nrows = int(np.ceil(len(methods_shap) / ncols))

    sns.set_style("whitegrid")
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, nrows * 3.5))
    fig.suptitle(
        "Figure 6 — Top 8 SHAP Features per Imputation Method\n"
        "(mean |SHAP| across 4 rolling-origin splits)",
        fontsize=12,
        fontweight="bold",
    )
    axes_flat = np.array(axes).flatten()

    for i, method in enumerate(methods_shap):
        ax = axes_flat[i]
        sub = shap_all[shap_all["method"] == method].nlargest(8, "mean_abs_shap")
        ax.barh(
            sub["feature"][::-1],
            sub["mean_abs_shap"][::-1],
            color="#4C9BE8",
            edgecolor="white",
            linewidth=0.5,
        )
        ax.set_title(method_pretty.get(method, method), fontsize=10, fontweight="bold")
        ax.set_xlabel("Mean |SHAP|", fontsize=8)
        ax.tick_params(axis="y", labelsize=7.5)
        ax.grid(axis="x", alpha=0.3)

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return True


def main() -> None:
    paths = build_paths()
    paths.results_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []

    # Load inputs
    t2_summary = safe_read_csv(paths.t2_summary, warnings)
    t2_bygap = safe_read_csv(paths.t2_bygap, warnings)
    t3_summary = safe_read_csv(paths.t3_summary, warnings)
    t3_detail = safe_read_csv(paths.t3_detail, warnings)
    t4_summary = safe_read_csv(paths.t4_summary, warnings)
    t4_per_split = safe_read_csv(paths.t4_per_split, warnings)

    meta = method_metadata()
    master = compute_master_comparison_table(meta, t2_summary, t3_summary, t4_summary, warnings)
    best_per_gap = compute_best_method_per_gap(t2_bygap, t3_detail, warnings)
    per_split_auc = compute_per_split_auc(t4_per_split, warnings)

    # Write tables
    master_path = paths.results_dir / "master_comparison_table.csv"
    best_gap_path = paths.results_dir / "best_method_per_gap.csv"
    split_auc_path = paths.results_dir / "per_split_auc.csv"
    warnings_path = paths.results_dir / "warnings.txt"

    master.to_csv(master_path, index=False)
    best_per_gap.to_csv(best_gap_path, index=False)
    per_split_auc.to_csv(split_auc_path, index=False)
    write_warnings(warnings_path, warnings)

    # Figures
    plot_fig1_rmse_mae(master, paths.figures_dir / "fig1_rmse_mae_comparison.png")
    plot_fig2_r2_heatmap(t2_bygap, t3_detail, paths.figures_dir / "fig2_r2_heatmap.png")
    plot_fig3_decay_curve(t2_bygap, t3_detail, paths.figures_dir / "fig3_performance_decay.png")
    plot_fig4_xgboost_auc_f1(master, paths.figures_dir / "fig4_xgboost_auc_f1.png")
    plot_fig5_auc_f1_per_split(t4_per_split, paths.figures_dir / "fig5_rolling_origin_splits.png")
    if not plot_fig6_shap_features(paths.t4_shap_dir, paths.figures_dir / "fig6_shap_features.png"):
        warnings.append("Could not generate Fig 6 (SHAP): no SHAP CSVs found/loaded.")
        write_warnings(warnings_path, warnings)

    # Console summary
    created = [
        master_path,
        best_gap_path,
        split_auc_path,
        warnings_path,
        paths.figures_dir / "fig1_rmse_mae_comparison.png",
        paths.figures_dir / "fig2_r2_heatmap.png",
        paths.figures_dir / "fig3_performance_decay.png",
        paths.figures_dir / "fig4_xgboost_auc_f1.png",
        paths.figures_dir / "fig5_rolling_origin_splits.png",
        paths.figures_dir / "fig6_shap_features.png",
    ]

    print("\nTask 5 outputs written:")
    for p in created:
        try:
            rel = p.relative_to(paths.root)
        except Exception:
            rel = p
        if p.exists():
            print(f"  ✓ {rel}")
        else:
            print(f"  ⚠️  expected but not found: {rel}")

    if warnings:
        print("\nWarnings were logged to:")
        print(f"  - {warnings_path.relative_to(paths.root)}")


if __name__ == "__main__":
    main()
