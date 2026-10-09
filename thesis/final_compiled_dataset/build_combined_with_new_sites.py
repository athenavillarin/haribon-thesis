"""
build_combined_with_new_sites.py
================================
Writes Combined_Labeled_2_0.csv: the 7 sites of Combined_Labeled_fixed.csv
plus Milagros (Masbate) and Cancabato Bay, through 2026-10-01.

Original-site labels keep the values in Combined_Labeled_fixed.csv. Days it
leaves unknown, and days after it ends, are filled from the BFAR OCR labels in
new_sites/western_visayas_daily_labels.csv and
new_sites/matarinao_dumanquillas_daily_labels.csv. The two sources agree on
98-100% of shared days for every site except Pilar (93%): for Pilar the OCR has
no ban in 2022-23 while the original data has bulletins showing one, so the
original labels are kept.

Environmental values after the end of each site's record, and values missing
in July-September 2026, come from new_sites/environment_tail.csv
(fetch_site_environment.py --tail).

New-site labels come from new_sites/candidate_site_daily_labels.csv (BFAR
bulletin OCR, state carried forward at most 45 days). Dates without a label
row are unknown and stay NaN. The raw bulletin column `red_tide` is left NaN
for the new sites except on the transition dates in
new_sites/candidate_site_transitions_for_spotcheck.csv, which are known bulletins.

Run fetch_site_environment.py --site for each new site and --tail first.

Usage:
    cd final_compiled_dataset
    python build_combined_with_new_sites.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fetch_site_environment import TAIL_PATH, environment_path

_THIS_DIR = Path(__file__).resolve().parent
NEW_DIR = _THIS_DIR / "new_sites"
BASE = _THIS_DIR / "Combined_Labeled_fixed.csv"
LABELS = NEW_DIR / "candidate_site_daily_labels.csv"
TRANSITIONS = NEW_DIR / "candidate_site_transitions_for_spotcheck.csv"
ORIGINAL_LABELS = [NEW_DIR / "western_visayas_daily_labels.csv", NEW_DIR / "matarinao_dumanquillas_daily_labels.csv"]
OCR_NAMES = {"Pilar (Capiz)": "Pilar"}
OUTPUT = _THIS_DIR / "Combined_Labeled_2_0.csv"

NEW_SITES = ["Milagros (Masbate)", "Cancabato Bay"]


def extend_with_tail(df: pd.DataFrame, tail: pd.DataFrame) -> pd.DataFrame:
    """Fill missing environmental values from the tail and append the days after the record ends."""
    keys = ["Location_Name", "Date"]
    env_cols = [c for c in tail.columns if c not in keys]
    merged = df.merge(tail, on=keys, how="outer", suffixes=("", "_tail"))
    for col in env_cols:
        merged[col] = merged[col].fillna(merged.pop(f"{col}_tail"))
    return merged[df.columns]


def fill_original_labels(df: pd.DataFrame) -> pd.Series:
    ocr = pd.concat([pd.read_csv(p, parse_dates=["date"]) for p in ORIGINAL_LABELS])
    ocr = ocr.rename(columns={"site": "Location_Name", "date": "Date", "label": "ocr"})
    ocr["Location_Name"] = ocr["Location_Name"].replace(OCR_NAMES)
    ocr = df[["Location_Name", "Date"]].merge(ocr, on=["Location_Name", "Date"], how="left")
    return df["red_tide_label"].fillna(pd.Series(ocr["ocr"].to_numpy(), index=df.index))


def main() -> None:
    tail = pd.read_csv(TAIL_PATH, parse_dates=["Date"])
    base = pd.read_csv(BASE, parse_dates=["Date"])
    base = extend_with_tail(base, tail[~tail["Location_Name"].isin(NEW_SITES)])
    base["red_tide_label"] = fill_original_labels(base)
    labels = pd.read_csv(LABELS, parse_dates=["date"]).rename(columns={"site": "Location_Name", "date": "Date"})
    transitions = pd.read_csv(TRANSITIONS, parse_dates=["bulletin_date"])
    transitions = transitions.rename(columns={"site": "Location_Name", "bulletin_date": "Date"})
    transitions["red_tide"] = (transitions.iloc[:, 2] == "P").astype(float)

    frames = [base]
    for site in NEW_SITES:
        env = pd.read_csv(environment_path(site), parse_dates=["Date"])
        env = extend_with_tail(env, tail[tail["Location_Name"] == site])
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
