"""
==============================================================================
HARIBON Red Tide Validation Study — Task 3: Spatial & Hybrid Imputation
==============================================================================
Purpose:
    Implement and validate spatial and hybrid imputation methods for missing
    data in environmental time series. This task extends Task 2's temporal
    methods by leveraging cross-location relationships and spatial patterns.

Imputation Methods:
    SPATIAL METHODS:
    1. CROSS-LOCATION LINEAR REGRESSION: Train model on one location to predict other
    2. CROSS-LOCATION KNN: Find K=5 similar days from other location
    3. DISTANCE-WEIGHTED AVERAGE: Weight by inverse geographic distance
    4. ADVECTION-BASED: Use wind/current vectors for transport prediction
    5. EOF/PCA SPATIAL MODES: Extract dominant spatial patterns
    6. SPATIAL KRIGING: Geostatistical interpolation for 2 locations
    
    HYBRID METHODS:
    7. SEQUENTIAL TEMPORAL->SPATIAL: Apply temporal first, spatial for remaining
    8. TEMPORAL-SPATIAL ENSEMBLE: Weighted average based on gap characteristics
    9. GAP-TYPE ADAPTIVE: Select method based on gap pattern

Validation Strategy:
    - Use artificially masked datasets from Task 1
    - Calculate RMSE, MAE, and R² against original values
    - Compare performance with Task 2 temporal methods

Input:
    ../task_1/task1_data/Task1_Combined_Baseline_Daily.csv (original data)
    ../task_1/masked_datasets/*/masked_data.csv (artificially gapped data)

Output:
    ../task3_results/
    ├── spatial_imputation_results.csv
    ├── method_comparison_metrics.csv
    ├── summary_table.csv
    └── validation_plots/

==============================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.decomposition import PCA
from scipy import stats
from scipy.spatial.distance import cdist
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input paths
TASK1_DATA_DIR = os.path.join("..", "task_1", "task1_data")
TASK1_MASKED_DIR = os.path.join("..", "task_1", "masked_datasets")
TASK2_RESULTS_DIR = os.path.join("..", "task_2", "task2_results")
BASELINE_FILE = "Task1_Combined_Baseline_Daily.csv"

# Output paths
OUTPUT_DIR = "task3_results"
RESULTS_FILE = "spatial_imputation_results.csv"
METRICS_FILE = "method_comparison_metrics.csv"
SUMMARY_FILE = "summary_table.csv"
SPATIAL_VS_TEMPORAL_FILE = "spatial_vs_temporal_comparison.csv"
HYBRID_FILE = "hybrid_performance.csv"

# Imputation methods
METHODS = {
    'cross_location_regression': 'Cross-Location Linear Regression',
    'cross_location_knn': 'Cross-Location KNN',
    'distance_weighted': 'Distance-Weighted Average',
    'advection': 'Advection-Based',
    'eof_pca': 'EOF/PCA Spatial Modes',
    'kriging': 'Spatial Kriging',
    'hybrid_sequential': 'Hybrid: Sequential Temporal->Spatial',
    'hybrid_ensemble': 'Hybrid: Temporal-Spatial Ensemble',
    'hybrid_adaptive': 'Hybrid: Gap-Type Adaptive'
}

# Variables to impute
VARIABLES_TO_IMPUTE = [
    'CHL', 'mlotst', 'no3', 'o2', 'po4', 'so', 'thetao', 'uo', 'vo',
    'NDVI_daily', 'NDVI_raw', 'precip_mm_day', 'wind_speed_ms',
    'wind_u_ms', 'wind_v_ms'
]

# Locations
LOCATIONS = ['Gigantes Polygon', 'Roxas Polygon']

# Geographic distance between locations (km)
DISTANCE_KM = 60.0

# Parameters
KNN_K = 5
TEMPORAL_DECAY = 0.95
LAG_DAYS = [1, 7]

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
        masked_data_path = os.path.join(TASK1_MASKED_DIR, mask_type, f"split_{split_num}", "masked_data.csv")
        config_path = os.path.join(TASK1_MASKED_DIR, mask_type, f"split_{split_num}", "config.json")
    else:
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type, "mask.csv")
        masked_data_path = os.path.join(TASK1_MASKED_DIR, mask_type, "masked_data.csv")
        config_path = os.path.join(TASK1_MASKED_DIR, mask_type, "config.json")
    
    # Load mask (boolean values indicating masked cells)
    mask_df = pd.read_csv(mask_path)
    
    # Load masked_data to get the actual Date column
    masked_data = pd.read_csv(masked_data_path)
    
    # Replace Date column in mask_df with actual dates from masked_data
    mask_df['Date'] = masked_data['Date']
    mask_df['Date'] = pd.to_datetime(mask_df['Date'])
    mask_df['Location_Name'] = masked_data['Location_Name']
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return mask_df, config

def get_other_location(location):
    """Get the other location name."""
    return [loc for loc in LOCATIONS if loc != location][0]

def calculate_metrics(y_true, y_pred):
    """Calculate RMSE, MAE, and R² metrics."""
    # Remove NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {'rmse': np.nan, 'mae': np.nan, 'r2': np.nan}
    
    rmse = np.sqrt(mean_squared_error(y_true_clean, y_pred_clean))
    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    
    # Handle R² calculation (can be negative)
    try:
        r2 = r2_score(y_true_clean, y_pred_clean)
    except:
        r2 = np.nan
    
    return {'rmse': rmse, 'mae': mae, 'r2': r2}

# =============================================================================
# SPATIAL IMPUTATION METHODS
# =============================================================================

def cross_location_regression_impute(data, variable, baseline_data, location):
    """
    Method 1: Cross-Location Linear Regression
    Train linear model on other location to predict missing values.
    """
    other_location = get_other_location(location)
    
    # Separate data by location
    data_loc = data[data['Location_Name'] == location].copy()
    data_other = data[data['Location_Name'] == other_location].copy()
    baseline_loc = baseline_data[baseline_data['Location_Name'] == location].copy()
    baseline_other = baseline_data[baseline_data['Location_Name'] == other_location].copy()
    
    # Merge on date
    merged = pd.merge(data_loc[['Date', variable]], data_other[['Date', variable]], 
                      on='Date', suffixes=('_loc', '_other'))
    baseline_merged = pd.merge(baseline_loc[['Date', variable]], baseline_other[['Date', variable]], 
                               on='Date', suffixes=('_loc', '_other'))
    
    # Create lagged features
    for lag in LAG_DAYS:
        merged[f'{variable}_other_lag{lag}'] = merged[f'{variable}_other'].shift(lag)
        baseline_merged[f'{variable}_other_lag{lag}'] = baseline_merged[f'{variable}_other'].shift(lag)
    
    # Train on baseline data where both locations have values
    feature_cols = [f'{variable}_other'] + [f'{variable}_other_lag{lag}' for lag in LAG_DAYS]
    train_mask = baseline_merged[feature_cols + [f'{variable}_loc']].notna().all(axis=1)
    
    if train_mask.sum() < 10:  # Need minimum training samples
        return data_loc[variable]
    
    X_train = baseline_merged.loc[train_mask, feature_cols].values
    y_train = baseline_merged.loc[train_mask, f'{variable}_loc'].values
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predict missing values
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    if missing_mask.sum() > 0:
        predict_data = merged.loc[missing_mask, feature_cols]
        predict_mask = predict_data.notna().all(axis=1)
        
        if predict_mask.sum() > 0:
            predictions = model.predict(predict_data.loc[predict_mask].values)
            result.loc[missing_mask & predict_mask] = predictions
    
    return result

def cross_location_knn_impute(data, variable, baseline_data, location):
    """
    Method 2: Cross-Location K-Nearest Neighbors
    Find K similar days from other location with temporal decay weighting.
    """
    other_location = get_other_location(location)
    
    data_loc = data[data['Location_Name'] == location].copy()
    data_other = data[data['Location_Name'] == other_location].copy()
    baseline_loc = baseline_data[baseline_data['Location_Name'] == location].copy()
    baseline_other = baseline_data[baseline_data['Location_Name'] == other_location].copy()
    
    # Merge on date
    merged = pd.merge(data_loc[['Date']], data_other[['Date', variable]], 
                      on='Date', how='left')
    
    # Use all available variables for similarity (not just target variable)
    feature_vars = [v for v in VARIABLES_TO_IMPUTE if v in data.columns]
    
    # Get training data from baseline (other location)
    train_data = baseline_other[['Date'] + feature_vars].copy()
    train_data = train_data.dropna(subset=feature_vars)
    
    if len(train_data) < KNN_K:
        return data_loc[variable]
    
    # Predict missing values
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    for idx in missing_mask[missing_mask].index:
        date = data_loc.loc[idx, 'Date']
        
        # Get features for this date from other location
        other_features = data_other[data_other['Date'] == date][feature_vars]
        
        if len(other_features) > 0 and other_features.notna().all(axis=1).any():
            # Calculate distances with temporal decay
            temporal_distances = np.abs((train_data['Date'] - date).dt.days)
            temporal_weights = TEMPORAL_DECAY ** temporal_distances
            
            # Feature distances
            feature_distances = cdist(other_features.iloc[[0]].values, 
                                     train_data[feature_vars].values, 
                                     metric='euclidean')[0]
            
            # Combined distance
            combined_distances = feature_distances / temporal_weights
            
            # Get K nearest neighbors
            k_indices = np.argsort(combined_distances)[:KNN_K]
            k_weights = 1 / (combined_distances[k_indices] + 1e-10)
            k_weights /= k_weights.sum()
            
            # Weighted average
            k_values = train_data.iloc[k_indices][variable].values
            if not np.isnan(k_values).all():
                result.loc[idx] = np.average(k_values[~np.isnan(k_values)], 
                                            weights=k_weights[~np.isnan(k_values)])
    
    return result

def distance_weighted_impute(data, variable, baseline_data, location):
    """
    Method 3: Distance-Weighted Average
    Weight observations by inverse geographic distance.
    """
    other_location = get_other_location(location)
    
    data_loc = data[data['Location_Name'] == location].copy()
    data_other = data[data['Location_Name'] == other_location].copy()
    
    # For single-location gaps, use 100% from other location
    merged = pd.merge(data_loc[['Date', variable]], data_other[['Date', variable]], 
                      on='Date', suffixes=('_loc', '_other'))
    
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    # Simple approach: use other location's value directly
    # (since we only have 2 locations, distance weighting is binary)
    result.loc[missing_mask] = merged.loc[missing_mask, f'{variable}_other'].values
    
    return result

def advection_impute(data, variable, baseline_data, location):
    """
    Method 4: Advection-Based Imputation
    Use wind/current vectors to estimate transport-based lag.
    """
    other_location = get_other_location(location)
    
    data_loc = data[data['Location_Name'] == location].copy()
    data_other = data[data['Location_Name'] == other_location].copy()
    baseline_loc = baseline_data[baseline_data['Location_Name'] == location].copy()
    baseline_other = baseline_data[baseline_data['Location_Name'] == other_location].copy()
    
    # Calculate advection-relevant velocity
    # Use wind speed for atmospheric variables, current speed for marine variables
    if variable in ['NDVI_daily', 'NDVI_raw', 'precip_mm_day', 'wind_speed_ms', 'wind_u_ms', 'wind_v_ms']:
        velocity_var = 'wind_speed_ms'
    else:
        # Calculate current speed from uo, vo
        velocity_var = None
        if 'uo' in data.columns and 'vo' in data.columns:
            data_loc['current_speed'] = np.sqrt(data_loc['uo']**2 + data_loc['vo']**2)
            data_other['current_speed'] = np.sqrt(data_other['uo']**2 + data_other['vo']**2)
            baseline_loc['current_speed'] = np.sqrt(baseline_loc['uo']**2 + baseline_loc['vo']**2)
            baseline_other['current_speed'] = np.sqrt(baseline_other['uo']**2 + baseline_other['vo']**2)
            velocity_var = 'current_speed'
    
    if velocity_var is None:
        # Fallback to simple cross-location
        return distance_weighted_impute(data, variable, baseline_data, location)
    
    # Estimate optimal lag from cross-correlation on baseline data
    baseline_merged = pd.merge(baseline_loc[['Date', variable, velocity_var]], 
                               baseline_other[['Date', variable, velocity_var]], 
                               on='Date', suffixes=('_loc', '_other'))
    
    # Find best lag (0 to 7 days)
    best_lag = 0
    best_corr = -1
    
    for lag in range(8):
        lagged = baseline_merged[f'{variable}_other'].shift(lag)
        mask = baseline_merged[f'{variable}_loc'].notna() & lagged.notna()
        
        if mask.sum() > 20:
            corr = np.corrcoef(baseline_merged.loc[mask, f'{variable}_loc'], 
                              lagged[mask])[0, 1]
            if not np.isnan(corr) and corr > best_corr:
                best_corr = corr
                best_lag = lag
    
    # Apply advection with optimal lag
    merged = pd.merge(data_loc[['Date', variable]], data_other[['Date', variable]], 
                      on='Date', suffixes=('_loc', '_other'))
    
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    # Shift other location by optimal lag
    lagged_values = merged[f'{variable}_other'].shift(best_lag)
    result.loc[missing_mask] = lagged_values.loc[missing_mask]
    
    return result

def eof_pca_impute(data, variable, baseline_data, location):
    """
    Method 5: EOF/PCA Spatial Modes
    Extract dominant spatial patterns and reconstruct missing values.
    """
    # Create wide format: dates × (locations × variables)
    data_pivot = data.pivot_table(index='Date', columns='Location_Name', values=VARIABLES_TO_IMPUTE)
    baseline_pivot = baseline_data.pivot_table(index='Date', columns='Location_Name', values=VARIABLES_TO_IMPUTE)
    
    # Flatten multi-index columns
    data_pivot.columns = ['_'.join(col).strip() for col in data_pivot.columns.values]
    baseline_pivot.columns = ['_'.join(col).strip() for col in baseline_pivot.columns.values]
    
    # Train PCA on baseline (complete data)
    baseline_clean = baseline_pivot.dropna()
    
    if len(baseline_clean) < 10:
        return data[data['Location_Name'] == location][variable]
    
    # Normalize
    mean = baseline_clean.mean()
    std = baseline_clean.std()
    baseline_normalized = (baseline_clean - mean) / (std + 1e-10)
    
    # Fit PCA (retain 95% variance)
    pca = PCA(n_components=0.95)
    pca.fit(baseline_normalized)
    
    # Reconstruct missing values
    target_col = f"{variable}_{location}"
    if target_col not in data_pivot.columns:
        return data[data['Location_Name'] == location][variable]
    
    result = data_pivot[target_col].copy()
    missing_mask = result.isna()
    
    for idx in missing_mask[missing_mask].index:
        row = data_pivot.loc[idx].copy()
        
        # If other columns available, reconstruct
        available_mask = row.notna()
        if available_mask.sum() >= len(available_mask) / 2:  # At least half available
            # Iterative reconstruction
            row_normalized = (row - mean) / (std + 1e-10)
            row_normalized[row.isna()] = 0  # Initialize missing with 0
            
            for _ in range(5):  # 5 iterations
                components = pca.transform(row_normalized.values.reshape(1, -1))
                reconstructed = pca.inverse_transform(components)
                row_normalized = pd.Series(reconstructed[0], index=row.index)
                row_normalized[available_mask] = (row[available_mask] - mean[available_mask]) / (std[available_mask] + 1e-10)
            
            # Denormalize
            reconstructed_value = row_normalized[target_col] * std[target_col] + mean[target_col]
            result.loc[idx] = reconstructed_value
    
    return result

def kriging_impute(data, variable, baseline_data, location):
    """
    Method 6: Spatial Kriging (2-point adaptation)
    Simple kriging for 2 locations based on temporal cross-correlation.
    """
    other_location = get_other_location(location)
    
    data_loc = data[data['Location_Name'] == location].copy()
    data_other = data[data['Location_Name'] == other_location].copy()
    baseline_loc = baseline_data[baseline_data['Location_Name'] == location].copy()
    baseline_other = baseline_data[baseline_data['Location_Name'] == other_location].copy()
    
    # Estimate spatial covariance from baseline
    baseline_merged = pd.merge(baseline_loc[['Date', variable]], baseline_other[['Date', variable]], 
                               on='Date', suffixes=('_loc', '_other'))
    baseline_merged = baseline_merged.dropna()
    
    if len(baseline_merged) < 20:
        return data_loc[variable]
    
    # Calculate covariance
    cov = np.cov(baseline_merged[f'{variable}_loc'], baseline_merged[f'{variable}_other'])[0, 1]
    var_loc = np.var(baseline_merged[f'{variable}_loc'])
    var_other = np.var(baseline_merged[f'{variable}_other'])
    
    # Kriging weight
    if var_other > 0:
        weight = cov / var_other
    else:
        weight = 0
    
    # Mean for each location
    mean_loc = baseline_merged[f'{variable}_loc'].mean()
    mean_other = baseline_merged[f'{variable}_other'].mean()
    
    # Apply kriging
    merged = pd.merge(data_loc[['Date', variable]], data_other[['Date', variable]], 
                      on='Date', suffixes=('_loc', '_other'))
    
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    # Kriging prediction: Y_loc = mean_loc + weight * (Y_other - mean_other)
    other_values = merged.loc[missing_mask, f'{variable}_other']
    kriging_pred = mean_loc + weight * (other_values - mean_other)
    result.loc[missing_mask] = kriging_pred
    
    return result

# =============================================================================
# HYBRID METHODS (Use Task 2 temporal methods)
# =============================================================================

def linear_interpolation_impute(data, variable):
    """Temporal method from Task 2: Linear interpolation."""
    imputed = data[variable].interpolate(method='linear', limit_direction='both')
    return imputed

def climatological_impute(data, variable, baseline_data):
    """Temporal method from Task 2: Climatological substitution."""
    # Compute day-of-year climatology
    baseline_data['day_of_year'] = baseline_data['Date'].dt.dayofyear
    climatology = baseline_data.groupby('day_of_year')[variable].mean()
    
    # Fill missing with climatology
    result = data[variable].copy()
    missing_mask = result.isna()
    
    data['day_of_year'] = data['Date'].dt.dayofyear
    for idx in missing_mask[missing_mask].index:
        doy = data.loc[idx, 'day_of_year']
        if doy in climatology.index:
            result.loc[idx] = climatology[doy]
    
    return result

def hybrid_sequential_impute(data, variable, baseline_data, location):
    """
    Hybrid 1: Sequential Temporal->Spatial
    Apply temporal interpolation first, then spatial for remaining gaps.
    """
    data_loc = data[data['Location_Name'] == location].copy().reset_index(drop=True)
    
    # Step 1: Temporal interpolation
    temporal_result = linear_interpolation_impute(data_loc, variable)
    
    # Step 2: Identify remaining gaps
    still_missing = temporal_result.isna()
    
    if still_missing.sum() == 0:
        return temporal_result
    
    # Step 3: Apply spatial method for remaining gaps
    # Create temporary data with temporal results
    temp_data = data.copy()
    temp_data.loc[temp_data['Location_Name'] == location, variable] = temporal_result
    
    spatial_result = cross_location_regression_impute(temp_data, variable, baseline_data, location)
    
    # Combine: use temporal where available, spatial for remaining
    result = temporal_result.copy()
    result.loc[still_missing] = spatial_result.loc[still_missing]
    
    return result

def hybrid_ensemble_impute(data, variable, baseline_data, location):
    """
    Hybrid 2: Temporal-Spatial Ensemble
    Weighted average based on gap characteristics.
    """
    data_loc = data[data['Location_Name'] == location].copy().reset_index(drop=True)
    
    # Get temporal prediction
    temporal_pred = linear_interpolation_impute(data_loc, variable)
    
    # Get spatial prediction
    spatial_pred = cross_location_regression_impute(data, variable, baseline_data, location)
    
    # Calculate gap sizes
    missing_mask = data_loc[variable].isna()
    gap_sizes = calculate_gap_sizes(missing_mask)
    
    # Adaptive weighting
    weights = np.ones(len(data_loc)) * 0.5  # Default balanced
    
    for idx, gap_size in gap_sizes.items():
        if gap_size < 3:
            weights[idx] = 0.8  # Favor temporal
        elif gap_size > 14:
            weights[idx] = 0.3  # Favor spatial
        # else: 0.5 (balanced)
    
    # Ensemble
    result = data_loc[variable].copy()
    missing_idx = missing_mask[missing_mask].index
    
    for idx in missing_idx:
        w = weights[idx]
        t_val = temporal_pred.loc[idx] if not np.isnan(temporal_pred.loc[idx]) else 0
        s_val = spatial_pred.loc[idx] if not np.isnan(spatial_pred.loc[idx]) else 0
        
        if not np.isnan(t_val) and not np.isnan(s_val):
            result.loc[idx] = w * t_val + (1 - w) * s_val
        elif not np.isnan(t_val):
            result.loc[idx] = t_val
        elif not np.isnan(s_val):
            result.loc[idx] = s_val
    
    return result

def hybrid_adaptive_impute(data, variable, baseline_data, location, mask_type):
    """
    Hybrid 3: Gap-Type Adaptive
    Select method based on gap pattern type.
    """
    data_loc = data[data['Location_Name'] == location].copy().reset_index(drop=True)
    
    # Select method based on mask type
    if 'random' in mask_type:
        # Random gaps: use temporal interpolation
        result = linear_interpolation_impute(data_loc, variable)
    elif 'block' in mask_type:
        # Block gaps: use spatial cross-location
        result = cross_location_regression_impute(data, variable, baseline_data, location)
    elif 'seasonal' in mask_type:
        # Seasonal gaps: climatology + spatial adjustment
        clim_result = climatological_impute(data_loc, variable, 
                                           baseline_data[baseline_data['Location_Name'] == location])
        spatial_result = cross_location_regression_impute(data, variable, baseline_data, location)
        
        # Average climatology and spatial
        result = data_loc[variable].copy()
        missing_mask = result.isna()
        result.loc[missing_mask] = (clim_result.loc[missing_mask] + spatial_result.loc[missing_mask]) / 2
    elif 'cross_variable' in mask_type:
        # Cross-variable gaps: use PCA
        result = eof_pca_impute(data, variable, baseline_data, location)
    else:
        # Default: sequential hybrid
        result = hybrid_sequential_impute(data, variable, baseline_data, location)
    
    return result

def calculate_gap_sizes(missing_mask):
    """Calculate size of gap for each missing value."""
    gap_sizes = {}
    current_gap_size = 0
    gap_indices = []
    
    for idx, is_missing in missing_mask.items():
        if is_missing:
            current_gap_size += 1
            gap_indices.append(idx)
        else:
            if current_gap_size > 0:
                for gap_idx in gap_indices:
                    gap_sizes[gap_idx] = current_gap_size
                current_gap_size = 0
                gap_indices = []
    
    # Handle final gap
    if current_gap_size > 0:
        for gap_idx in gap_indices:
            gap_sizes[gap_idx] = current_gap_size
    
    return gap_sizes

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_imputation(masked_data, imputed_data, baseline_data, mask_info, variable, location):
    """Validate imputation against ground truth."""
    # Get mask for this variable and location
    mask_df = mask_info[0]
    mask_loc = mask_df[mask_df['Location_Name'] == location].copy().reset_index(drop=True)
    baseline_loc = baseline_data[baseline_data['Location_Name'] == location].copy().reset_index(drop=True)
    imputed_data_reset = imputed_data.copy().reset_index(drop=True)
    
    # Merge to align dates
    merged = pd.merge(
        mask_loc[['Date', variable]].rename(columns={variable: 'is_masked'}),
        baseline_loc[['Date', variable]].rename(columns={variable: 'true_value'}),
        on='Date',
        how='inner'
    )
    merged = pd.merge(
        merged,
        imputed_data_reset[['Date', variable]].rename(columns={variable: 'imputed_value'}),
        on='Date',
        how='inner'
    )
    
    # Calculate metrics only on masked values (where is_masked == True)
    masked_points = merged[merged['is_masked'] == True].copy()
    
    if len(masked_points) == 0:
        return {'rmse': np.nan, 'mae': np.nan, 'r2': np.nan, 'count': 0}
    
    metrics = calculate_metrics(masked_points['true_value'].values, 
                                masked_points['imputed_value'].values)
    metrics['count'] = len(masked_points)
    
    return metrics
    
    return metrics

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def discover_masked_datasets():
    """Discover all masked datasets from Task 1."""
    datasets = []
    
    for mask_type in os.listdir(TASK1_MASKED_DIR):
        mask_path = os.path.join(TASK1_MASKED_DIR, mask_type)
        
        if not os.path.isdir(mask_path):
            continue
        
        if 'rolling_origin' in mask_type:
            # Has splits
            for split in os.listdir(mask_path):
                split_path = os.path.join(mask_path, split)
                if os.path.isdir(split_path) and 'split_' in split:
                    split_num = split.split('_')[1]
                    datasets.append((mask_type, int(split_num)))
        else:
            # No splits
            datasets.append((mask_type, None))
    
    return sorted(datasets)

def run_imputation_analysis():
    """Main function to run all imputation methods."""
    print("="*70)
    print("HARIBON Red Tide Validation Study - Task 3")
    print("Spatial & Hybrid Imputation Methods")
    print("="*70)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load baseline data
    print("\nLoading baseline data...")
    baseline_data = load_baseline_data()
    print(f"  Loaded {len(baseline_data)} records from {len(baseline_data['Location_Name'].unique())} locations")
    
    # Discover masked datasets
    print("\nDiscovering masked datasets...")
    datasets = discover_masked_datasets()
    print(f"  Found {len(datasets)} datasets")
    
    # Run imputation for each method, dataset, variable, and location
    all_results = []
    total_iterations = len(datasets) * len(METHODS) * len(VARIABLES_TO_IMPUTE) * len(LOCATIONS)
    current_iteration = 0
    
    for mask_type, split_num in datasets:
        print(f"\n{'-'*70}")
        print(f"Processing: {mask_type}" + (f" - Split {split_num}" if split_num else ""))
        print(f"{'-'*70}")
        
        # Load masked data
        masked_data = load_masked_dataset(mask_type, split_num)
        mask_info = get_mask_info(mask_type, split_num)
        
        for method_key, method_name in METHODS.items():
            print(f"\n  Method: {method_name}")
            
            for variable in VARIABLES_TO_IMPUTE:
                for location in LOCATIONS:
                    current_iteration += 1
                    progress = (current_iteration / total_iterations) * 100
                    
                    print(f"    [{progress:5.1f}%] {variable} @ {location[:10]}...", end=' ')
                    
                    try:
                        # Apply imputation method
                        if method_key == 'cross_location_regression':
                            imputed = cross_location_regression_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'cross_location_knn':
                            imputed = cross_location_knn_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'distance_weighted':
                            imputed = distance_weighted_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'advection':
                            imputed = advection_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'eof_pca':
                            imputed = eof_pca_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'kriging':
                            imputed = kriging_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'hybrid_sequential':
                            imputed = hybrid_sequential_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'hybrid_ensemble':
                            imputed = hybrid_ensemble_impute(masked_data, variable, baseline_data, location)
                        elif method_key == 'hybrid_adaptive':
                            imputed = hybrid_adaptive_impute(masked_data, variable, baseline_data, location, mask_type)
                        else:
                            print("SKIP")
                            continue
                        
                        # Create imputed dataframe
                        imputed_data = masked_data[masked_data['Location_Name'] == location][['Date']].copy().reset_index(drop=True)
                        
                        # Ensure imputed is a Series or convert to Series if needed
                        if isinstance(imputed, pd.Series):
                            imputed_data[variable] = imputed.reset_index(drop=True).values
                        else:
                            imputed_data[variable] = imputed
                        
                        # Validate
                        metrics = validate_imputation(masked_data, imputed_data, baseline_data, 
                                                     mask_info, variable, location)
                        
                        # Store result
                        result = {
                            'mask_type': mask_type,
                            'split_num': split_num if split_num else 0,
                            'method': method_key,
                            'method_name': method_name,
                            'variable': variable,
                            'location': location,
                            'rmse': metrics['rmse'],
                            'mae': metrics['mae'],
                            'r2': metrics['r2'],
                            'missing_count': metrics['count']
                        }
                        all_results.append(result)
                        
                        print(f"RMSE: {metrics['rmse']:.3f}")
                        
                    except Exception as e:
                        # Store failed result with NaN
                        result = {
                            'mask_type': mask_type,
                            'split_num': split_num if split_num else 0,
                            'method': method_key,
                            'method_name': method_name,
                            'variable': variable,
                            'location': location,
                            'rmse': np.nan,
                            'mae': np.nan,
                            'r2': np.nan,
                            'missing_count': 0
                        }
                        all_results.append(result)
                        print(f"ERROR: {str(e)[:70]}")
    
    # Save results
    print(f"\n{'='*70}")
    print("Saving results...")
    results_df = pd.DataFrame(all_results)
    results_path = os.path.join(OUTPUT_DIR, RESULTS_FILE)
    results_df.to_csv(results_path, index=False)
    print(f"  Saved {len(results_df)} results to {RESULTS_FILE}")
    
    # Generate summary statistics
    print("\nGenerating summary statistics...")
    
    # Method comparison
    method_metrics = results_df.groupby(['method', 'method_name']).agg({
        'rmse': ['mean', 'std', 'min', 'max'],
        'mae': ['mean', 'std', 'min', 'max'],
        'r2': ['mean', 'std', 'min', 'max']
    }).round(4)
    method_metrics.to_csv(os.path.join(OUTPUT_DIR, METRICS_FILE))
    print(f"  Saved method comparison to {METRICS_FILE}")
    
    # Overall summary
    summary = results_df.groupby('method_name').agg({
        'rmse': 'mean',
        'mae': 'mean',
        'r2': 'mean',
        'missing_count': 'sum'
    }).round(4).sort_values('rmse')
    summary.to_csv(os.path.join(OUTPUT_DIR, SUMMARY_FILE))
    print(f"  Saved summary table to {SUMMARY_FILE}")
    
    print(f"\n{'='*70}")
    print("Task 3 Spatial Imputation Complete!")
    print(f"{'='*70}")
    
    return results_df

if __name__ == "__main__":
    results = run_imputation_analysis()
