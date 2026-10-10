"""
plot_model_comparison.py
========================
Bar chart of all-site AUC and per-site AUC for every model in the results
tables (thesis Fig. 4.6). Reads the saved summaries, so nothing is retrained.

Usage:
    cd evaluation
    python plot_model_comparison.py

Output:
    results/figures/model_comparison_auc.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
OUTPUT = RESULTS_DIR / "figures" / "model_comparison_auc.png"

# (summary file, model key, label, group)
ROWS = [
    ("leakfree", "climatology", "Site rate by month\n(baseline)", "baseline"),
    ("leakfree", "xgboost", "XGBoost\n(raw inputs)", "raw"),
    ("leakfree", "lstm", "LSTM\n(raw inputs)", "raw"),
    ("leakfree", "gru", "GRU\n(raw inputs)", "raw"),
    ("leakfree", "transformer", "Transformer\n(raw inputs)", "raw"),
    ("dl_anomaly", "lstm", "LSTM\n(anomaly features)", "anomaly"),
    ("dl_anomaly", "gru", "GRU\n(anomaly features)", "anomaly"),
    ("dl_anomaly", "transformer", "Transformer\n(anomaly features)", "anomaly"),
    ("dl_anomaly", "env_model", "Logistic\nregression", "anomaly"),
    ("dl_anomaly", "dl_lr", "Ensemble\n(deployed)", "ensemble"),
]
COLORS = {"baseline": "#9e9e9e", "raw": "#e0a458", "anomaly": "#5b8fc7", "ensemble": "#1f4e8c"}


def load_rows() -> pd.DataFrame:
    summaries = {name: pd.read_csv(RESULTS_DIR / f"{name}_summary.csv").set_index("model")
                 for name in {r[0] for r in ROWS}}
    return pd.DataFrame([
        {"label": label, "group": group,
         "auc": summaries[src].loc[key, "pooled_auc_mean"],
         "per_site_auc": summaries[src].loc[key, "per_site_auc_mean"]}
        for src, key, label, group in ROWS
    ])


def main() -> None:
    df = load_rows()
    baseline_site = df.loc[df["group"] == "baseline", "per_site_auc"].iloc[0]
    x = np.arange(len(df))
    width = 0.38
    colors = df["group"].map(COLORS)

    fig, ax = plt.subplots(figsize=(13, 5.5))
    bars_all = ax.bar(x - width / 2, df["auc"], width, color=colors, edgecolor="black", linewidth=0.5)
    bars_site = ax.bar(x + width / 2, df["per_site_auc"], width, color=colors, edgecolor="black",
                       linewidth=0.5, hatch="///", alpha=0.75)
    for bars in (bars_all, bars_site):
        ax.bar_label(bars, fmt="%.3f", fontsize=7.5, padding=2)

    ax.axhline(0.5, color="red", linestyle="--", linewidth=1)
    ax.axhline(baseline_site, color="#555555", linestyle=":", linewidth=1.2)

    ax.set_xticks(x, df["label"], fontsize=8.5)
    ax.set_ylim(0.3, 0.9)
    ax.set_ylabel("Mean AUC over 6 rolling-origin splits")
    ax.set_title("All-site AUC and per-site AUC by model")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="white", edgecolor="black", label="All-site AUC"),
        Patch(facecolor="white", edgecolor="black", hatch="///", label="Per-site AUC"),
        Patch(facecolor=COLORS["baseline"], label="Baseline"),
        Patch(facecolor=COLORS["raw"], label="Raw daily inputs"),
        Patch(facecolor=COLORS["anomaly"], label="Anomaly features"),
        Patch(facecolor=COLORS["ensemble"], label="Ensemble (deployed)"),
        Line2D([], [], color="#555555", linestyle=":", label=f"Baseline per-site AUC ({baseline_site:.3f})"),
        Line2D([], [], color="red", linestyle="--", label="Random chance (0.5)"),
    ], loc="upper left", fontsize=8, ncol=4)

    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
