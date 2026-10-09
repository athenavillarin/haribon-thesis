"""
fix_date_swap.py
================
Builds Combined_Labeled_fixed.csv from Combined_Labeled.csv.

In Combined_Labeled.csv every value on a day 1-12 (where day != month) belongs
to the date with month and day swapped: the row for 2020-03-01 holds the data
for 2020-01-03. This affects all environmental variables and the raw bulletin
column `red_tide`. Verified against the sources for Matarinao Bay, 2020:
  - GLORYS thetao/so, nearest grid cell: 182/182 days match exactly once unswapped
  - CMEMS CHL (+-0.1 deg box): corr 0.65 as stored, 1.00 unswapped
  - CHIRPS precipitation (5 km buffer): corr 0.42 as stored, 0.99 unswapped

`red_tide_label` was densified from the swapped bulletins, so it is rebuilt
from the unswapped bulletins: each bulletin state is carried forward until the
next bulletin, for at most 45 days, and days beyond that are left unknown.
This is the same convention as the candidate-site labels from the BFAR OCR.

Rows whose swap partner falls outside the record are set to NaN.

Usage:
    cd final_compiled_dataset
    python fix_date_swap.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_THIS_DIR = Path(__file__).resolve().parent
SOURCE = _THIS_DIR / "Combined_Labeled.csv"
OUTPUT = _THIS_DIR / "Combined_Labeled_fixed.csv"

SWAPPED_COLUMNS = [
    "red_tide", "CHL", "NDVI_daily", "NDVI_raw", "mlotst", "precip_mm_day",
    "so", "thetao", "uo", "vo", "wind_speed_ms", "wind_u_ms", "wind_v_ms",
]
CARRY_FORWARD_DAYS = 45


def swapped_date(dates: pd.Series) -> pd.Series:
    """Date with month and day exchanged, for days 1-12 where day != month; otherwise the date itself."""
    affected = (dates.dt.day <= 12) & (dates.dt.day != dates.dt.month)
    partner = pd.to_datetime(
        dict(year=dates.dt.year, month=dates.dt.day.where(affected, dates.dt.month),
             day=dates.dt.month.where(affected, dates.dt.day)),
    )
    return partner


def unswap(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    lookup = df.set_index(["Location_Name", "Date"])[SWAPPED_COLUMNS]
    keys = pd.MultiIndex.from_arrays([df["Location_Name"], swapped_date(df["Date"])])
    df[SWAPPED_COLUMNS] = lookup.reindex(keys).to_numpy()
    return df


def densify_labels(df: pd.DataFrame) -> pd.Series:
    """Carry each bulletin state forward to the next bulletin, for at most CARRY_FORWARD_DAYS."""
    labels = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby("Location_Name", sort=False):
        bulletin_date = g["Date"].where(g["red_tide"].notna()).ffill()
        state = g["red_tide"].ffill()
        age = (g["Date"] - bulletin_date).dt.days
        labels.loc[g.index] = state.where(age < CARRY_FORWARD_DAYS)
    return labels


def main() -> None:
    df = pd.read_csv(SOURCE, parse_dates=["Date"]).sort_values(["Location_Name", "Date"]).reset_index(drop=True)
    fixed = unswap(df)
    fixed["red_tide_label"] = densify_labels(fixed)
    fixed.to_csv(OUTPUT, index=False)

    affected = (swapped_date(df["Date"]) != df["Date"]).mean()
    print(f"Rows with a swapped date: {affected:.1%}")
    print(f"Wrote {OUTPUT.name}: {len(fixed):,} rows")


if __name__ == "__main__":
    main()
