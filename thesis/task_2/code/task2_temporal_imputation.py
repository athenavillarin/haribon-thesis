"""
==============================================================================
HARIBON Red Tide Validation Study — Task 2: Temporal Imputation Methods
==============================================================================
Purpose:
    Implement and validate temporal imputation methods for missing data in
    environmental time series. This task focuses on time-based imputation
    techniques that leverage temporal patterns in the data.

Imputation Methods:
    1. LINEAR INTERPOLATION: Uses linear interpolation between known values
       to fill gaps. Best for short gaps where the relationship is approximately
       linear.

    2. CLIMATOLOGICAL SUBSTITUTION: Replaces missing values with the long-term
       average for that day-of-year across all available years. Useful for
       seasonal/cyclical data.

Validation Strategy:
    - Use artificially masked datasets from Task 1
    - Calculate RMSE, MAE, and R² against original values
    - Compare performance across different gap patterns

Input:
    task_1/task1_data/Task1_Combined_Baseline_Daily.csv (original data)
    task_1/masked_datasets/*/masked_data.csv (artificially gapped data)

Output:
    task2_results/
    ├── temporal_imputation_results.csv
    ├── method_comparison_metrics.csv
    └── validation_plots/

==============================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input paths
TASK1_DATA_DIR = "../../task_1/task1_data"
TASK1_MASKED_DIR = "../../task_1/masked_datasets"
BASELINE_FILE = "Task1_Combined_Baseline_Daily.csv"

# Output paths
OUTPUT_DIR = "../task2_results"
RESULTS_FILE = "temporal_imputation_results.csv"
METRICS_FILE = "method_comparison_metrics.csv"
PLOTS_DIR = "validation_plots"

# Imputation methods
METHODS = {
    'linear_interpolation': 'Linear Interpolation',
    'climatological': 'Climatological Substitution'
}

# Variables to impute (exclude Location_Name and Date)
VARIABLES_TO_IMPUTE = [
    'CHL', 'mlotst', 'no3', 'o2', 'po4', 'so', 'thetao', 'uo', 'vo',
    'NDVI_daily', 'NDVI_raw', 'precip_mm_day', 'wind_speed_ms',
    'wind_u_ms', 'wind_v_ms'
]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_baseline_data():
    """Load the original baseline dataset."""
    baseline_path = os.path.join(TASK1_DATA_DIR, BASELINE_FILE)
    df = pd.read_csv(baseline_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def load_masked_dataset(mask_type, split_num=None):
    """Load a specific masked dataset."""
    if split_num:
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type, f"split_{split_num}", "masked_data.csv")
    else:
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type, "masked_data.csv")

    df = pd.read_csv(mask_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def get_mask_info(mask_type, split_num=None):
    """Load mask information for a dataset."""
    if split_num:
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type, f"split_{split_num}", "mask.csv")
        config_path = os.path.join(TASK1_MASKED_DIR, mask_type, f"split_{split_num}", "config.json")
    else:
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type, "mask.csv")
        config_path = os.path.join(TASK1_MASKED_DIR, mask_type, "config.json")

    mask_df = pd.read_csv(mask_path)
    with open(config_path, 'r') as f:
        config = json.load(f)

    return mask_df, config

def calculate_metrics(true_values, predicted_values):
    """Calculate RMSE, MAE, and R² for imputation accuracy."""
    # Remove NaN values for fair comparison
    valid_idx = ~(np.isnan(true_values) | np.isnan(predicted_values))
    if np.sum(valid_idx) == 0:
        return {'rmse': np.nan, 'mae': np.nan, 'r2': np.nan}

    true_clean = true_values[valid_idx]
    pred_clean = predicted_values[valid_idx]

    rmse = np.sqrt(mean_squared_error(true_clean, pred_clean))
    mae = mean_absolute_error(true_clean, pred_clean)
    r2 = r2_score(true_clean, pred_clean)

    return {'rmse': rmse, 'mae': mae, 'r2': r2}

# =============================================================================
# IMPUTATION METHODS
# =============================================================================

def linear_interpolation_impute(data, variable):
    """
    Perform linear interpolation imputation for a single variable.

    Args:
        data: DataFrame with time series data
        variable: Column name to impute

    Returns:
        Series with imputed values
    """
    # Create a copy to avoid modifying original
    imputed = data[variable].copy()

    # Linear interpolation
    imputed = imputed.interpolate(method='linear', limit_direction='both')

    return imputed

def climatological_substitution_impute(data, variable, baseline_data):
    """
    Perform climatological substitution imputation for a single variable.

    This method replaces missing values with the long-term average for that
    day-of-year across all available years.

    Args:
        data: DataFrame with time series data (may have gaps)
        variable: Column name to impute
        baseline_data: Complete baseline DataFrame for computing climatology

    Returns:
        Series with imputed values
    """
    # Create a copy to avoid modifying original
    imputed = data[variable].copy()

    # Compute day-of-year climatology from baseline data
    baseline_copy = baseline_data.copy()
    baseline_copy['day_of_year'] = baseline_copy['Date'].dt.dayofyear
    baseline_copy['year'] = baseline_copy['Date'].dt.year

    # Group by day of year and compute mean, ignoring NaN
    climatology = baseline_copy.groupby('day_of_year')[variable].mean()

    # For each missing value, substitute with climatological average
    missing_mask = imputed.isna()
    if missing_mask.any():
        day_of_year_missing = data.loc[missing_mask, 'Date'].dt.dayofyear
        imputed.loc[missing_mask] = climatology.loc[day_of_year_missing].values

    return imputed

def impute_dataset(data, baseline_data, method):
    """
    Apply imputation method to all variables in a dataset.

    Args:
        data: DataFrame with missing values
        baseline_data: Complete baseline DataFrame
        method: Imputation method ('linear_interpolation' or 'climatological')

    Returns:
        DataFrame with imputed values
    """
    imputed_data = data.copy()

    for variable in VARIABLES_TO_IMPUTE:
        if method == 'linear_interpolation':
            imputed_data[variable] = linear_interpolation_impute(data, variable)
        elif method == 'climatological':
            imputed_data[variable] = climatological_substitution_impute(data, variable, baseline_data)
        else:
            raise ValueError(f"Unknown imputation method: {method}")

    return imputed_data

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_imputation(masked_data, imputed_data, baseline_data, mask_info):
    """
    Validate imputation accuracy against original values.

    Args:
        masked_data: Original data with artificial gaps
        imputed_data: Data after imputation
        baseline_data: Complete baseline data (ground truth)
        mask_info: Information about which values were masked

    Returns:
        Dictionary with validation metrics
    """
    results = {}

    # Ensure we're comparing the same locations and dates
    merged = pd.merge(
        masked_data[['Location_Name', 'Date']],
        baseline_data,
        on=['Location_Name', 'Date'],
        how='left'
    )

    for variable in VARIABLES_TO_IMPUTE:
        # Find where this variable was masked (missing in masked_data)
        missing_mask = masked_data[variable].isna()

        if missing_mask.sum() > 0:
            # Get true values for missing positions
            true_values = merged.loc[missing_mask, variable].values
            imputed_values = imputed_data.loc[missing_mask, variable].values

            # Calculate metrics
            metrics = calculate_metrics(true_values, imputed_values)
            results[variable] = metrics
        else:
            results[variable] = {'rmse': np.nan, 'mae': np.nan, 'r2': np.nan}

    return results

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("Starting Task 2: Temporal Imputation Methods")
    print("=" * 60)

    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, PLOTS_DIR), exist_ok=True)

    # Load baseline data
    print("Loading baseline data...")
    baseline_data = load_baseline_data()
    print(f"Baseline data shape: {baseline_data.shape}")
    print(f"Date range: {baseline_data['Date'].min()} to {baseline_data['Date'].max()}")

    # Get list of masked datasets
    masked_datasets = []
    for item in os.listdir(TASK1_MASKED_DIR):
        item_path = os.path.join(TASK1_MASKED_DIR, item)
        if os.path.isdir(item_path):
            if item.startswith('rolling_origin'):
                # Handle rolling origin splits
                for split_dir in os.listdir(item_path):
                    if split_dir.startswith('split_'):
                        masked_datasets.append((item, split_dir.split('_')[1]))
            else:
                masked_datasets.append((item, None))

    print(f"Found {len(masked_datasets)} masked datasets to process")

    # Results storage
    all_results = []

    # Process each masked dataset
    for mask_type, split_num in masked_datasets:
        print(f"\nProcessing {mask_type}" + (f" (split {split_num})" if split_num else ""))

        # Load masked data
        masked_data = load_masked_dataset(mask_type, split_num)

        # Load mask information
        mask_df, config = get_mask_info(mask_type, split_num)

        # Apply each imputation method
        for method_key, method_name in METHODS.items():
            print(f"  Applying {method_name}...")

            # Impute missing values
            imputed_data = impute_dataset(masked_data, baseline_data, method_key)

            # Validate imputation
            validation_results = validate_imputation(
                masked_data, imputed_data, baseline_data, (mask_df, config)
            )

            # Store results
            for variable, metrics in validation_results.items():
                result = {
                    'mask_type': mask_type,
                    'split_num': split_num,
                    'method': method_key,
                    'method_name': method_name,
                    'variable': variable,
                    'rmse': metrics['rmse'],
                    'mae': metrics['mae'],
                    'r2': metrics['r2'],
                    'missing_count': mask_df[variable].sum() if variable in mask_df.columns else 0
                }
                all_results.append(result)

    # Save results
    results_df = pd.DataFrame(all_results)
    results_path = os.path.join(OUTPUT_DIR, RESULTS_FILE)
    results_df.to_csv(results_path, index=False)
    print(f"\nDetailed results saved to: {results_path}")

    # Create summary metrics by method and mask type
    summary_metrics = results_df.groupby(['method_name', 'mask_type']).agg({
        'rmse': ['mean', 'std'],
        'mae': ['mean', 'std'],
        'r2': ['mean', 'std']
    }).round(4)

    # Flatten column names
    summary_metrics.columns = ['_'.join(col).strip() for col in summary_metrics.columns]
    summary_metrics = summary_metrics.reset_index()

    summary_path = os.path.join(OUTPUT_DIR, METRICS_FILE)
    summary_metrics.to_csv(summary_path, index=False)
    print(f"Summary metrics saved to: {summary_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY OF TEMPORAL IMPUTATION RESULTS")
    print("=" * 60)

    for method in METHODS.values():
        print(f"\n{method}:")
        method_data = summary_metrics[summary_metrics['method_name'] == method]
        for _, row in method_data.iterrows():
            print(f"  {row['mask_type']}:")
            print(".4f")
            print(".4f")
            print(".4f")

    print(f"\nTask 2 completed successfully!")
    print(f"Results saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()