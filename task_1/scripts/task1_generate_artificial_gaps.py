"""
==============================================================================
HARIBON Red Tide Validation Study — Task 1: Artificial Gap Generation
==============================================================================
Purpose:
    Create reproducible artificial gaps in the gap-free baseline dataset to
    enable validation of imputation methods. The original data is NEVER
    modified — only masked copies are produced.

Masking Strategies:
    1. RANDOM (10%, 20%): Uniformly distributed missing values.
    2. BLOCK (7-day, 14-day): Consecutive missing periods simulating sensor
       outages or extended cloud cover.
    3. SEASONAL: Higher missingness during monsoon (Jun-Oct) reflecting
       real-world cloud coverage patterns.
    4. CROSS-VARIABLE: Entire variable columns missing for periods, simulating
       sensor-specific failures.
    5. ROLLING-ORIGIN: Time-based train/test splits for temporal validation.

Output Structure:
    masked_datasets/
    ├── random_10/
    │   ├── masked_data.csv
    │   ├── mask.csv
    │   └── config.json
    ├── random_20/
    ├── block_7day/
    ├── block_14day/
    ├── seasonal/
    ├── cross_variable/
    └── rolling_origin/

==============================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

RANDOM_SEED = 42
INPUT_DIR = "task1_data"
INPUT_FILE = "Task1_Combined_Baseline_Daily.csv"
OUTPUT_BASE_DIR = "masked_datasets"

# Variables to mask (exclude identifiers)
EXCLUDE_COLS = ["Location_Name", "Date"]

# Masking configurations
MASK_CONFIGS = {
    "random_10": {
        "type": "random",
        "missing_rate": 0.10,
        "description": "10% uniformly random missing values"
    },
    "random_20": {
        "type": "random",
        "missing_rate": 0.20,
        "description": "20% uniformly random missing values"
    },
    "block_7day": {
        "type": "block",
        "block_length": 7,
        "num_blocks_per_location": 8,  # ~56 days per location over 4 years
        "description": "7-day consecutive gaps simulating week-long outages"
    },
    "block_14day": {
        "type": "block",
        "block_length": 14,
        "num_blocks_per_location": 4,  # ~56 days per location over 4 years
        "description": "14-day consecutive gaps simulating extended outages"
    },
    "seasonal": {
        "type": "seasonal",
        "habagat_rate": 0.40,   # Jun-Oct: high cloud cover
        "amihan_rate": 0.10,   # Nov-May: clear skies
        "description": "Seasonal missingness: 40% during Habagat (Jun-Oct), 10% during Amihan (Nov-May)"
    },
    "cross_variable": {
        "type": "cross_variable",
        "variables_to_mask": ["CHL", "NDVI_daily", "NDVI_raw"],
        "mask_periods": [
            {"start": "2020-06-01", "end": "2020-06-30"},  # 1 month CHL outage
            {"start": "2021-08-01", "end": "2021-09-15"},  # 1.5 month outage
        ],
        "description": "Entire variable columns missing for specific periods (sensor failures)"
    },
    "rolling_origin": {
        "type": "rolling_origin",
        "test_window_days": 90,  # 3-month test windows
        "num_splits": 4,
        "description": "Rolling-origin cross-validation: progressive train/test splits"
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_ground_truth(input_path: str) -> pd.DataFrame:
    """Load the ground truth dataset (never modify original)."""
    df = pd.read_csv(input_path)
    df["Date"] = pd.to_datetime(df["Date"])
    print(f"Loaded ground truth: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def get_maskable_columns(df: pd.DataFrame) -> list:
    """Get list of columns that should be masked (exclude identifiers)."""
    return [col for col in df.columns if col not in EXCLUDE_COLS]


def create_random_mask(df: pd.DataFrame, missing_rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """
    Create random missing mask.
    Returns: DataFrame of same shape with True = missing (to be masked).
    """
    cols = get_maskable_columns(df)
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    
    for col in cols:
        # Only mask cells that have actual data (not already NaN)
        valid_mask = df[col].notna()
        valid_indices = df.index[valid_mask].tolist()
        
        if len(valid_indices) > 0:
            n_to_mask = int(len(valid_indices) * missing_rate)
            indices_to_mask = rng.choice(valid_indices, size=n_to_mask, replace=False)
            mask.loc[indices_to_mask, col] = True
    
    return mask


def create_block_mask(df: pd.DataFrame, block_length: int, num_blocks_per_location: int, 
                      rng: np.random.Generator) -> pd.DataFrame:
    """
    Create block (consecutive) missing mask.
    Places num_blocks_per_location blocks of block_length days per location.
    """
    cols = get_maskable_columns(df)
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    
    locations = df["Location_Name"].unique()
    
    for loc in locations:
        loc_indices = df.index[df["Location_Name"] == loc].tolist()
        n_days = len(loc_indices)
        
        if n_days < block_length:
            continue
        
        # For each variable, place blocks at random starting positions
        for col in cols:
            valid_in_loc = df.loc[loc_indices, col].notna()
            valid_indices = [idx for idx in loc_indices if df.loc[idx, col] == df.loc[idx, col]]  # not NaN
            
            if len(valid_indices) < block_length:
                continue
            
            # Choose random starting positions for blocks
            max_start = len(loc_indices) - block_length
            if max_start <= 0:
                continue
            
            # Ensure blocks don't overlap excessively
            block_starts = []
            attempts = 0
            while len(block_starts) < num_blocks_per_location and attempts < 100:
                start_pos = rng.integers(0, max_start)
                # Check for overlap with existing blocks
                overlap = False
                for existing_start in block_starts:
                    if abs(start_pos - existing_start) < block_length:
                        overlap = True
                        break
                if not overlap:
                    block_starts.append(start_pos)
                attempts += 1
            
            # Apply blocks
            for start_pos in block_starts:
                block_indices = loc_indices[start_pos:start_pos + block_length]
                mask.loc[block_indices, col] = True
    
    return mask


def create_seasonal_mask(df: pd.DataFrame, habagat_rate: float, amihan_rate: float,
                         rng: np.random.Generator) -> pd.DataFrame:
    """
    Create seasonal missing mask reflecting Philippine monsoon patterns.
    Habagat (SW Monsoon): June-October (higher cloud cover)
    Amihan (NE Monsoon): November-May (clearer skies)
    """
    cols = get_maskable_columns(df)
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    
    months = df["Date"].dt.month
    is_habagat = months.isin([6, 7, 8, 9, 10])  # Jun-Oct
    
    for col in cols:
        valid_mask = df[col].notna()
        
        # Habagat season
        habagat_valid = df.index[valid_mask & is_habagat].tolist()
        if len(habagat_valid) > 0:
            n_mask = int(len(habagat_valid) * habagat_rate)
            to_mask = rng.choice(habagat_valid, size=n_mask, replace=False)
            mask.loc[to_mask, col] = True
        
        # Amihan season
        amihan_valid = df.index[valid_mask & ~is_habagat].tolist()
        if len(amihan_valid) > 0:
            n_mask = int(len(amihan_valid) * amihan_rate)
            to_mask = rng.choice(amihan_valid, size=n_mask, replace=False)
            mask.loc[to_mask, col] = True
    
    return mask


def create_cross_variable_mask(df: pd.DataFrame, variables: list, 
                                periods: list) -> pd.DataFrame:
    """
    Create cross-variable mask: entire columns missing for specific periods.
    Simulates sensor-specific outages.
    """
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    
    for period in periods:
        start = pd.to_datetime(period["start"])
        end = pd.to_datetime(period["end"])
        
        period_mask = (df["Date"] >= start) & (df["Date"] <= end)
        
        for var in variables:
            if var in df.columns:
                mask.loc[period_mask, var] = True
    
    return mask


def create_rolling_origin_masks(df: pd.DataFrame, test_window_days: int, 
                                 num_splits: int) -> dict:
    """
    Create rolling-origin cross-validation masks.
    Returns dict of {split_name: mask_df}
    
    Each split uses all data before a cutoff as "training" (unmasked)
    and test_window_days after cutoff as "test" (masked).
    """
    cols = get_maskable_columns(df)
    masks = {}
    
    # Get date range
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    total_days = (max_date - min_date).days
    
    # Create evenly spaced cutoff points
    # Leave room for test window at the end
    available_range = total_days - test_window_days
    step = available_range // (num_splits + 1)
    
    for i in range(num_splits):
        split_name = f"split_{i+1}"
        
        # Cutoff date
        cutoff_days = step * (i + 1)
        cutoff_date = min_date + pd.Timedelta(days=cutoff_days)
        test_end_date = cutoff_date + pd.Timedelta(days=test_window_days)
        
        # Mask = True for test period
        mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        test_period = (df["Date"] > cutoff_date) & (df["Date"] <= test_end_date)
        
        for col in cols:
            mask.loc[test_period, col] = True
        
        masks[split_name] = {
            "mask": mask,
            "cutoff_date": str(cutoff_date.date()),
            "test_start": str((cutoff_date + pd.Timedelta(days=1)).date()),
            "test_end": str(test_end_date.date())
        }
    
    return masks


def apply_mask(df: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """Apply mask to dataframe: set masked cells to NaN."""
    masked_df = df.copy()
    masked_df = masked_df.where(~mask, other=np.nan)
    
    # Restore identifier columns
    masked_df["Location_Name"] = df["Location_Name"]
    masked_df["Date"] = df["Date"]
    
    return masked_df


def compute_mask_stats(df: pd.DataFrame, mask: pd.DataFrame) -> dict:
    """Compute statistics about the mask."""
    cols = get_maskable_columns(df)
    
    stats = {
        "total_cells": 0,
        "masked_cells": 0,
        "original_nan_cells": 0,
        "per_variable": {}
    }
    
    for col in cols:
        total = len(df)
        original_nan = int(df[col].isna().sum())
        masked = int(mask[col].sum())
        
        stats["total_cells"] += total
        stats["masked_cells"] += masked
        stats["original_nan_cells"] += original_nan
        stats["per_variable"][col] = {
            "total": int(total),
            "original_nan": int(original_nan),
            "artificially_masked": int(masked),
            "mask_rate": round(float(masked / (total - original_nan) * 100), 2) if (total - original_nan) > 0 else 0.0
        }
    
    stats["total_cells"] = int(stats["total_cells"])
    stats["masked_cells"] = int(stats["masked_cells"])
    stats["original_nan_cells"] = int(stats["original_nan_cells"])
    stats["overall_mask_rate"] = round(
        float(stats["masked_cells"] / (stats["total_cells"] - stats["original_nan_cells"]) * 100), 2
    ) if (stats["total_cells"] - stats["original_nan_cells"]) > 0 else 0.0
    
    return stats


def save_outputs(output_dir: str, masked_df: pd.DataFrame, mask: pd.DataFrame, 
                 config: dict, stats: dict):
    """Save masked data, mask, and configuration to output directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save masked data
    masked_df_out = masked_df.copy()
    masked_df_out["Date"] = masked_df_out["Date"].dt.strftime("%Y-%m-%d")
    masked_df_out.to_csv(os.path.join(output_dir, "masked_data.csv"), index=False)
    
    # Save mask (boolean)
    mask.to_csv(os.path.join(output_dir, "mask.csv"), index=False)
    
    # Save configuration and stats
    full_config = {
        "config": config,
        "stats": stats,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "random_seed": RANDOM_SEED,
            "source_file": INPUT_FILE
        }
    }
    with open(os.path.join(output_dir, "config.json"), "w") as f:
        json.dump(full_config, f, indent=2)
    
    print(f"  Saved to: {output_dir}")
    print(f"  Overall mask rate: {stats['overall_mask_rate']}%")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("=" * 70)
    print("HARIBON Task 1: Artificial Gap Generation")
    print("=" * 70)
    
    # Set global random seed
    rng = np.random.default_rng(RANDOM_SEED)
    print(f"\nRandom seed: {RANDOM_SEED}")
    
    # Load ground truth
    input_path = os.path.join(INPUT_DIR, INPUT_FILE)
    df = load_ground_truth(input_path)
    
    # Create output base directory
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # Process each masking strategy
    for mask_name, config in MASK_CONFIGS.items():
        print(f"\n{'─' * 50}")
        print(f"Generating: {mask_name}")
        print(f"  Type: {config['type']}")
        print(f"  Description: {config['description']}")
        
        mask_type = config["type"]
        output_dir = os.path.join(OUTPUT_BASE_DIR, mask_name)
        
        if mask_type == "random":
            mask = create_random_mask(df, config["missing_rate"], rng)
            masked_df = apply_mask(df, mask)
            stats = compute_mask_stats(df, mask)
            save_outputs(output_dir, masked_df, mask, config, stats)
        
        elif mask_type == "block":
            mask = create_block_mask(df, config["block_length"], 
                                     config["num_blocks_per_location"], rng)
            masked_df = apply_mask(df, mask)
            stats = compute_mask_stats(df, mask)
            save_outputs(output_dir, masked_df, mask, config, stats)
        
        elif mask_type == "seasonal":
            mask = create_seasonal_mask(df, config["habagat_rate"], 
                                        config["amihan_rate"], rng)
            masked_df = apply_mask(df, mask)
            stats = compute_mask_stats(df, mask)
            save_outputs(output_dir, masked_df, mask, config, stats)
        
        elif mask_type == "cross_variable":
            mask = create_cross_variable_mask(df, config["variables_to_mask"],
                                               config["mask_periods"])
            masked_df = apply_mask(df, mask)
            stats = compute_mask_stats(df, mask)
            save_outputs(output_dir, masked_df, mask, config, stats)
        
        elif mask_type == "rolling_origin":
            rolling_masks = create_rolling_origin_masks(df, config["test_window_days"],
                                                         config["num_splits"])
            
            for split_name, split_data in rolling_masks.items():
                split_dir = os.path.join(output_dir, split_name)
                mask = split_data["mask"]
                masked_df = apply_mask(df, mask)
                stats = compute_mask_stats(df, mask)
                
                # Add split-specific info to config
                split_config = config.copy()
                split_config["cutoff_date"] = split_data["cutoff_date"]
                split_config["test_start"] = split_data["test_start"]
                split_config["test_end"] = split_data["test_end"]
                
                save_outputs(split_dir, masked_df, mask, split_config, stats)
    
    print(f"\n{'=' * 70}")
    print("Gap generation complete!")
    print(f"Output directory: {OUTPUT_BASE_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()
