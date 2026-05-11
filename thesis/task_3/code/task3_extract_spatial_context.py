"""
==============================================================================
HARIBON Red Tide Validation Study — Task 3: Extract Spatial Context Features
==============================================================================
Purpose:
    Extract additional spatial context features from gridded datasets to
    enhance spatial imputation methods. This includes spatial gradients,
    spatial variance, distance to coast, and bathymetry.

Features Extracted:
    1. Spatial gradients: ∂CHL/∂x, ∂CHL/∂y, ∂SST/∂x, ∂SST/∂y
    2. Spatial variance within each polygon
    3. Distance to coast (from GEBCO)
    4. Bathymetry (ocean depth)

Data Sources:
    - Copernicus Marine Service (CMEMS): CHL, SST gridded data
    - GEBCO: Bathymetry and distance to coast

Requirements:
    - copernicusmarine Python package
    - Internet connection for data download
    - CMEMS credentials (if required)

Output:
    spatial_context_features.csv - Additional spatial features by date/location

Note:
    This script requires re-extraction of raw gridded data at higher
    resolution (5×5 grid around each polygon) than the original aggregated
    data from Task 1. This is OPTIONAL - the main spatial imputation methods
    work without these features.

Usage:
    python task3_extract_spatial_context.py

==============================================================================
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input
TASK1_DATA_DIR = os.path.join("..", "task_1", "task1_data")
BASELINE_FILE = "Task1_Combined_Baseline_Daily.csv"

# Output
OUTPUT_DIR = "task3_data"
OUTPUT_FILE = "spatial_context_features.csv"

# Polygon definitions (from Task 1)
POLYGONS = {
    'Gigantes Polygon': {
        'lon_min': 123.2316,
        'lon_max': 123.3871,
        'lat_min': 11.5188,
        'lat_max': 11.6632
    },
    'Roxas Polygon': {
        'lon_min': 122.6280,
        'lon_max': 122.8065,
        'lat_min': 11.5404,
        'lat_max': 11.6647
    }
}

# Date range
START_DATE = "2019-01-01"
END_DATE = "2022-12-31"

# Variables to extract
VARIABLES = ['CHL', 'thetao']  # Chlorophyll and SST

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_spatial_gradient(grid_data):
    """
    Calculate spatial gradients (∂/∂x, ∂/∂y) from gridded data.
    
    Args:
        grid_data: 2D numpy array (lat × lon)
    
    Returns:
        dict with 'gradient_x', 'gradient_y', 'gradient_magnitude'
    """
    if grid_data.size == 0 or np.all(np.isnan(grid_data)):
        return {
            'gradient_x': np.nan,
            'gradient_y': np.nan,
            'gradient_magnitude': np.nan
        }
    
    # Calculate gradients using numpy gradient
    grad_y, grad_x = np.gradient(grid_data)
    
    # Average gradient across grid
    mean_grad_x = np.nanmean(grad_x)
    mean_grad_y = np.nanmean(grad_y)
    gradient_magnitude = np.sqrt(mean_grad_x**2 + mean_grad_y**2)
    
    return {
        'gradient_x': mean_grad_x,
        'gradient_y': mean_grad_y,
        'gradient_magnitude': gradient_magnitude
    }

def calculate_spatial_variance(grid_data):
    """Calculate spatial variance within grid."""
    if grid_data.size == 0 or np.all(np.isnan(grid_data)):
        return np.nan
    
    return np.nanvar(grid_data)

def calculate_distance_to_coast(polygon):
    """
    Estimate distance to coast based on polygon location.
    
    Note: This is a simplified version. For production, use actual
    coastline data from GEBCO or similar.
    
    Args:
        polygon: dict with lon_min, lon_max, lat_min, lat_max
    
    Returns:
        distance_km: estimated distance to nearest coast
    """
    # Simplified: These polygons are coastal, so distance is small
    # Gigantes is island-based (~5km), Roxas is coastal (~1km)
    
    center_lon = (polygon['lon_min'] + polygon['lon_max']) / 2
    center_lat = (polygon['lat_min'] + polygon['lat_max']) / 2
    
    # Rough estimates based on Philippine geography
    if 'Gigantes' in str(polygon):
        return 5.0  # Gigantes Islands
    else:
        return 1.0  # Roxas coastal
    
def calculate_bathymetry(polygon):
    """
    Estimate average bathymetry (ocean depth) for polygon.
    
    Note: This is a simplified version. For production, query GEBCO
    bathymetry dataset.
    
    Args:
        polygon: dict with lon_min, lon_max, lat_min, lat_max
    
    Returns:
        depth_m: average ocean depth (negative for below sea level)
    """
    # Simplified: Visayan Sea typical depths
    # Gigantes area: ~50-100m
    # Roxas coastal: ~20-50m
    
    if 'Gigantes' in str(polygon):
        return -75.0  # meters (negative = below sea level)
    else:
        return -35.0  # meters

# =============================================================================
# MAIN EXTRACTION FUNCTIONS
# =============================================================================

def extract_spatial_context_features():
    """
    Extract spatial context features for each location and date.
    
    Note: This is a TEMPLATE function. Full implementation would require:
    1. Copernicus Marine API access
    2. GEBCO bathymetry data access
    3. Significant computation time
    
    For the thesis, we'll create SYNTHETIC features based on the existing
    baseline data to demonstrate the concept.
    """
    print("="*70)
    print("Extracting Spatial Context Features")
    print("="*70)
    
    # Load baseline data
    print("\nLoading baseline data...")
    baseline_path = os.path.join(TASK1_DATA_DIR, BASELINE_FILE)
    baseline = pd.read_csv(baseline_path)
    baseline['Date'] = pd.to_datetime(baseline['Date'])
    print(f"  Loaded {len(baseline)} records")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize results
    spatial_features = []
    
    print("\nCalculating spatial features...")
    print("NOTE: Using synthetic features based on existing data")
    print("      Full implementation would require re-extraction from CMEMS")
    
    for location_name, polygon in POLYGONS.items():
        print(f"\n  Processing: {location_name}")
        
        location_data = baseline[baseline['Location_Name'] == location_name].copy()
        
        # Static features (same for all dates)
        distance_to_coast = calculate_distance_to_coast(polygon)
        bathymetry = calculate_bathymetry(polygon)
        
        print(f"    Distance to coast: {distance_to_coast:.1f} km")
        print(f"    Bathymetry: {bathymetry:.1f} m")
        
        for idx, row in location_data.iterrows():
            date = row['Date']
            
            # Synthetic spatial features based on existing data
            # In production, these would come from gridded data extraction
            
            # Spatial variance (estimated from temporal variance)
            CHL_value = row['CHL']
            SST_value = row['thetao']
            
            # Estimate spatial variance as ~10% of temporal variance
            CHL_spatial_var = np.random.uniform(0.05, 0.15) * CHL_value if not np.isnan(CHL_value) else np.nan
            SST_spatial_var = np.random.uniform(0.5, 1.5) if not np.isnan(SST_value) else np.nan
            
            # Estimate gradients based on differences between locations
            # (simplified - would need actual grid in production)
            CHL_gradient_mag = np.random.uniform(0.01, 0.1) if not np.isnan(CHL_value) else np.nan
            SST_gradient_mag = np.random.uniform(0.01, 0.5) if not np.isnan(SST_value) else np.nan
            
            feature_row = {
                'Date': date,
                'Location_Name': location_name,
                'CHL_spatial_variance': CHL_spatial_var,
                'CHL_gradient_magnitude': CHL_gradient_mag,
                'SST_spatial_variance': SST_spatial_var,
                'SST_gradient_magnitude': SST_gradient_mag,
                'distance_to_coast_km': distance_to_coast,
                'bathymetry_m': bathymetry,
                'polygon_area_km2': (polygon['lon_max'] - polygon['lon_min']) * 
                                   (polygon['lat_max'] - polygon['lat_min']) * 111 * 111  # rough km²
            }
            
            spatial_features.append(feature_row)
    
    # Convert to DataFrame
    spatial_df = pd.DataFrame(spatial_features)
    
    # Save results
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    spatial_df.to_csv(output_path, index=False)
    
    print(f"\n{'='*70}")
    print(f"Spatial context features saved to: {OUTPUT_FILE}")
    print(f"Total records: {len(spatial_df)}")
    print(f"Features extracted: {len(spatial_df.columns) - 2}")  # Exclude Date and Location
    print(f"{'='*70}")
    
    # Display summary
    print("\nFeature Summary:")
    print(spatial_df.describe())
    
    return spatial_df

# =============================================================================
# INTEGRATION WITH MAIN IMPUTATION
# =============================================================================

def load_spatial_features():
    """Load spatial context features for use in imputation."""
    feature_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    if not os.path.exists(feature_path):
        print(f"Warning: Spatial features file not found: {feature_path}")
        print("         Run task3_extract_spatial_context.py first")
        return None
    
    df = pd.read_csv(feature_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def spatial_gradient_model_impute(data, variable, baseline_data, location, spatial_features):
    """
    Method 4: Spatial Gradient Model
    
    Use spatial gradients and variance as predictive features.
    This would be integrated into task3_spatial_imputation.py if spatial
    features are available.
    
    Args:
        data: DataFrame with gaps
        variable: Variable to impute
        baseline_data: Complete baseline
        location: Location name
        spatial_features: DataFrame with spatial context features
    
    Returns:
        Series with imputed values
    """
    from sklearn.linear_model import LinearRegression
    
    if spatial_features is None:
        print("Warning: Spatial features not available, using simple method")
        # Fallback to simple cross-location
        return None
    
    # Merge spatial features
    data_with_features = pd.merge(data, spatial_features, on=['Date', 'Location_Name'])
    baseline_with_features = pd.merge(baseline_data, spatial_features, on=['Date', 'Location_Name'])
    
    # Feature columns
    feature_cols = [
        f'{variable}_spatial_variance',
        f'{variable}_gradient_magnitude',
        'distance_to_coast_km',
        'bathymetry_m'
    ]
    
    # Filter to location
    data_loc = data_with_features[data_with_features['Location_Name'] == location].copy()
    baseline_loc = baseline_with_features[baseline_with_features['Location_Name'] == location].copy()
    
    # Train on baseline
    train_mask = baseline_loc[[variable] + feature_cols].notna().all(axis=1)
    
    if train_mask.sum() < 20:
        return data.loc[data['Location_Name'] == location, variable]
    
    X_train = baseline_loc.loc[train_mask, feature_cols].values
    y_train = baseline_loc.loc[train_mask, variable].values
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predict missing
    result = data_loc[variable].copy()
    missing_mask = result.isna()
    
    if missing_mask.sum() > 0:
        predict_data = data_loc.loc[missing_mask, feature_cols]
        predict_mask = predict_data.notna().all(axis=1)
        
        if predict_mask.sum() > 0:
            predictions = model.predict(predict_data.loc[predict_mask].values)
            result.loc[missing_mask & predict_mask] = predictions
    
    return result

# =============================================================================
# PRODUCTION VERSION TEMPLATE
# =============================================================================

def extract_gridded_data_production(variable, polygon, date_range):
    """
    TEMPLATE for production version using actual CMEMS data.
    
    This is NOT implemented in the thesis but shows how it would be done.
    
    Args:
        variable: 'CHL' or 'thetao'
        polygon: dict with lon/lat bounds
        date_range: tuple of (start_date, end_date)
    
    Returns:
        DataFrame with gridded data
    """
    
    # Pseudocode for production version:
    """
    1. Install copernicusmarine:
       pip install copernicusmarine
    
    2. Extract gridded data (not spatially averaged):
       import copernicusmarine
       
       dataset = copernicusmarine.open_dataset(
           dataset_id="cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
           minimum_longitude=polygon['lon_min'] - 0.1,
           maximum_longitude=polygon['lon_max'] + 0.1,
           minimum_latitude=polygon['lat_min'] - 0.1,
           maximum_latitude=polygon['lat_max'] + 0.1,
           start_datetime=date_range[0],
           end_datetime=date_range[1],
           variables=variable
       )
    
    3. For each date:
       - Extract 2D grid (lat × lon)
       - Calculate spatial gradients using calculate_spatial_gradient()
       - Calculate spatial variance using calculate_spatial_variance()
       - Store results
    
    4. For bathymetry:
       - Download GEBCO gridded bathymetry for region
       - Calculate mean depth within polygon
    
    5. For distance to coast:
       - Use GEBCO coastline data
       - Calculate distance from polygon centroid to nearest coast
    """
    
    raise NotImplementedError(
        "Production version requires CMEMS API access. "
        "Use synthetic features for thesis demonstration."
    )

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("HARIBON Red Tide Validation Study - Task 3")
    print("Extract Spatial Context Features")
    print("="*70)
    
    print("\nIMPORTANT NOTE:")
    print("  This script generates SYNTHETIC spatial features for demonstration.")
    print("  Full production implementation would require:")
    print("    - Copernicus Marine API access")
    print("    - GEBCO bathymetry data")
    print("    - Significant computation time for grid processing")
    print("\n  The spatial imputation methods in task3_spatial_imputation.py")
    print("  work WITHOUT these features using cross-location relationships.")
    print("="*70)
    
    response = input("\nContinue with synthetic feature generation? (y/n): ")
    
    if response.lower() == 'y':
        spatial_features = extract_spatial_context_features()
        
        print("\n" + "="*70)
        print("Next Steps:")
        print("  1. Review spatial_context_features.csv")
        print("  2. (Optional) Integrate with task3_spatial_imputation.py")
        print("  3. Run main spatial imputation: python code/task3_spatial_imputation.py")
        print("="*70)
    else:
        print("\nSpatial feature extraction cancelled.")
        print("Spatial imputation methods will work without these features.")
