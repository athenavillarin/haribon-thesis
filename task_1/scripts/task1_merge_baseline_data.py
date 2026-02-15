"""
==============================================================================
HARIBON Red Tide Validation Study — Task 1: Merge Baseline Datasets
==============================================================================
Purpose:
    Combine Marine and Atmospheric baseline datasets into a single unified
    CSV for the Imputation & Validation framework.

Input:
    task1_data/Task1_Marine_Baseline_Daily.csv
    task1_data/Task1_Atmospheric_Baseline_Daily.csv

Output:
    task1_data/Task1_Combined_Baseline_Daily.csv
==============================================================================
"""
import pandas as pd
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = "task1_data"
MARINE_FILE = "Task1_Marine_Baseline_Daily.csv"
ATMOSPHERIC_FILE = "Task1_Atmospheric_Baseline_Daily.csv"
OUTPUT_FILE = "Task1_Combined_Baseline_Daily.csv"

# =============================================================================
# MERGE DATASETS
# =============================================================================

# Load both datasets
marine = pd.read_csv(os.path.join(DATA_DIR, MARINE_FILE))
atmospheric = pd.read_csv(os.path.join(DATA_DIR, ATMOSPHERIC_FILE))

print(f"Marine dataset: {marine.shape}")
print(f"Atmospheric dataset: {atmospheric.shape}")

# Merge on Location_Name and Date
merged = pd.merge(marine, atmospheric, on=["Location_Name", "Date"], how="outer")

# Sort by location and date
merged = merged.sort_values(["Location_Name", "Date"]).reset_index(drop=True)

# Save the combined dataset
output_path = os.path.join(DATA_DIR, OUTPUT_FILE)
merged.to_csv(output_path, index=False)

print(f"\nMerged dataset saved to: {output_path}")
print(f"Combined shape: {merged.shape}")
print(f"\nColumns ({len(merged.columns)}): {list(merged.columns)}")
