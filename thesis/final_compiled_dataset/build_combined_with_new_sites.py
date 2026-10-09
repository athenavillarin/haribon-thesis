"""
build_combined_with_new_sites.py
================================
Writes Combined_Labeled_2_0.csv: the 7 sites of Combined_Labeled_fixed.csv
plus Milagros (Masbate) and Cancabato Bay.

New-site labels come from new_sites/candidate_site_daily_labels.csv (BFAR
bulletin OCR, state carried forward at most 45 days). Dates without a label
row are unknown and stay NaN. The raw bulletin column `red_tide` is left NaN
for the new sites except on the transition dates in
new_sites/candidate_site_transitions_for_spotcheck.csv, which are known bulletins.

Run fetch_site_environment.py for each new site first.

Usage:
    cd final_compiled_dataset
    python build_combined_with_new_sites.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fetch_site_environment import environment_path

_THIS_DIR = Path(__file__).resolve().parent
NEW_DIR = _THIS_DIR / "new_sites"
BASE = _THIS_DIR / "Combined_Labeled_fixed.csv"
LABELS = NEW_DIR / "candidate_site_daily_labels.csv"
TRANSITIONS = NEW_DIR / "candidate_site_transitions_for_spotcheck.csv"
OUTPUT = _THIS_DIR / "Combined_Labeled_2_0.csv"

NEW_SITES = ["Milagros (Masbate)", "Cancabato Bay"]


def main() -> None:
    base = pd.read_csv(BASE, parse_dates=["Date"])
    labels = pd.read_csv(LABELS, parse_dates=["date"]).rename(columns={"site": "Location_Name", "date": "Date"})
    transitions = pd.read_csv(TRANSITIONS, parse_dates=["bulletin_date"])
    transitions = transitions.rename(columns={"site": "Location_Name", "bulletin_date": "Date"})
    transitions["red_tide"] = (transitions.iloc[:, 2] == "P").astype(float)

    frames = [base]
    for site in NEW_SITES:
        env = pd.read_csv(environment_path(site), parse_dates=["Date"])
        site_labels = labels[labels["Location_Name"] == site][["Date", "red_tide_label"]]
        bulletins = transitions[transitions["Location_Name"] == site][["Date", "red_tide"]]
        env = env.merge(site_labels, on="Date", how="left").merge(bulletins, on="Date", how="left")
        frames.append(env[base.columns])

    combined = pd.concat(frames, ignore_index=True).sort_values(["Location_Name", "Date"])
    combined.to_csv(OUTPUT, index=False)
    summary = combined.groupby("Location_Name").agg(
        rows=("Date", "size"), labelled=("red_tide_label", "count"), positive_share=("red_tide_label", "mean"))
    print(f"Wrote {OUTPUT.name}: {len(combined):,} rows")
    print(summary.round(3).to_string())


if __name__ == "__main__":
    main()
