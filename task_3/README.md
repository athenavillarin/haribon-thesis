# HARIBON Red Tide Validation Study - Task 3: Spatial & Hybrid Imputation Methods

## Overview
Task 3 implements and validates spatial and hybrid imputation methods for handling missing data in environmental time series. This task extends Task 2's temporal methods by leveraging cross-location relationships, spatial patterns, and hybrid temporal-spatial approaches.

## Quick Start

### Run Complete Task 3 Analysis
```bash
cd task_3
python run_task3.py
```

This will execute spatial imputation analysis, hybrid methods, and generate all validation plots.

### Individual Steps
```bash
# Step 1: Extract spatial context features (optional - requires data access)
python code/task3_extract_spatial_context.py

# Step 2: Run spatial imputation analysis
python code/task3_spatial_imputation.py

# Step 3: Generate validation plots
python code/task3_validation_plots.py
```

## Spatial Imputation Methods Implemented

### Understanding Spatial Structure
**Key Insight**: The HARIBON dataset consists of 2 spatially-aggregated polygon locations (Gigantes and Roxas in Capiz Province, Philippines), approximately 60km apart. Traditional pixel-based spatial interpolation isn't applicable, so we leverage **cross-location relationships** and **spatial covariates**.

### Simple Spatial Methods

#### 1. Cross-Location Linear Regression
- **Description**: Train linear model using data from one location to predict the other
- **Features**: Same variable, same dates, with lagged features (t-1, t-7 days)
- **Best for**: Variables with strong cross-location correlation (e.g., regional weather patterns)
- **Implementation**: `sklearn.linear_model.LinearRegression`

**Mathematical Formulation**:
```
Y_Gigantes(t) = β₀ + β₁·Y_Roxas(t) + β₂·Y_Roxas(t-1) + β₃·Y_Roxas(t-7) + ε
```

#### 2. Cross-Location K-Nearest Neighbors
- **Description**: Find K=5 most similar days from the other location based on available variables
- **Weighting**: Temporal distance decay factor α=0.95
- **Best for**: Non-linear relationships, capturing complex spatial patterns
- **Implementation**: `sklearn.neighbors.KNeighborsRegressor`

**Distance Metric**:
```
d(t₁, t₂) = √(Σ(X_i(t₁) - X_i(t₂))²) × α^|t₁-t₂|
```

#### 3. Distance-Weighted Average
- **Description**: Weight observations by inverse geographic distance (~60km between sites)
- **Strategy**: For single-location gaps, use 100% from other location
- **Best for**: Spatially homogeneous variables (e.g., large-scale ocean features)

**Weighting**:
```
Y_A(t) = (w_A·Y_A(t) + w_B·Y_B(t)) / (w_A + w_B)
where w = 1 / distance²
```

### External Spatial Predictors

#### 4. Spatial Gradient Model
- **Description**: Extract gridded CHL/SST from 5×5 grid around each polygon
- **Features**: 
  - Spatial gradients: ∂CHL/∂x, ∂CHL/∂y, ∂SST/∂x, ∂SST/∂y
  - Spatial variance within polygon
  - Distance-to-coast, bathymetry from GEBCO
- **Best for**: Variables with strong spatial gradients (e.g., coastal upwelling zones)
- **Note**: Requires re-extraction of raw gridded data

**Model**:
```
CHL_imputed = f(spatial_variance, gradient_magnitude, distance_between_sites)
```

### Vector Field Methods

#### 5. Advection-Based Imputation
- **Description**: Use wind `(wind_u_ms, wind_v_ms)` and current `(uo, vo)` vectors for transport-based prediction
- **Approach**: Track backward from location B to estimate location A
- **Best for**: Advection-dominated variables (CHL, SST)

**Simple Advection**:
```
CHL(A, t) ≈ CHL(B, t - Δt)
where Δt = distance / |velocity|
```

**Time-Lagged Correlation**:
```
Find optimal lag τ that maximizes: corr(Y_A(t), Y_B(t-τ))
```

#### 6. EOF/PCA Spatial Modes
- **Description**: Empirical Orthogonal Function analysis on 2-location × 16-variable matrix
- **Strategy**: Extract dominant spatial patterns, reconstruct missing values
- **Variance retention**: Keep modes explaining 95% of variance
- **Best for**: Multi-variable gaps, capturing coupled ocean-atmosphere patterns

**Reconstruction**:
```
Y = Σ(λᵢ · EOFᵢ)  where λᵢ are principal components
```

### Advanced Methods

#### 7. Spatial Kriging (2-Point Adaptation)
- **Description**: Geostatistical interpolation adapted for 2 locations
- **Approach**: Model spatial covariance from temporal cross-correlation
- **Output**: Predictions with uncertainty bounds
- **Best for**: Providing confidence intervals for imputed values

**Kriging Equations**:
```
Ŷ(x₀) = Σ λᵢ·Y(xᵢ)  
subject to: Σ λᵢ = 1
minimizing: σ²(x₀) = var(Ŷ(x₀) - Y(x₀))
```

#### 8. Dynamic Factor Model
- **Description**: State-space model assuming shared latent spatial factor
- **Implementation**: EM algorithm or Kalman filter
- **Best for**: Capturing time-varying spatial relationships
- **Library**: `statsmodels` or `pykalman`

**State-Space Model**:
```
Observation: Y[location,t] = B × factor[t] + ε
State: factor[t] = Φ × factor[t-1] + η
```

## Hybrid Temporal-Spatial Methods

### Hybrid 1: Sequential Temporal→Spatial
- **Strategy**: Apply Task 2's linear interpolation first, then spatial methods for remaining gaps
- **Rationale**: Temporal methods excel at short gaps; spatial methods handle endpoints/long gaps
- **Best for**: Mixed gap patterns with both short and long missing periods

**Algorithm**:
```
1. Apply linear interpolation to all gaps
2. Identify remaining gaps (edges, failed interpolations)
3. Apply spatial cross-location method to remaining gaps
```

### Hybrid 2: Temporal-Spatial Ensemble
- **Strategy**: Weighted average of temporal and spatial predictions
- **Adaptive weighting**: Based on gap characteristics
  - w = 0.8 for gaps < 3 days (favor temporal)
  - w = 0.5 for gaps 3-14 days (balanced)
  - w = 0.3 for gaps > 14 days (favor spatial)
- **Best for**: Maximizing robustness across all gap types

**Ensemble**:
```
Y_imputed = w × Y_temporal + (1-w) × Y_spatial
```

### Hybrid 3: Gap-Type Adaptive
- **Strategy**: Select method based on gap pattern
  - Random gaps: Linear interpolation
  - Block gaps: Spatial cross-location
  - Seasonal gaps: Climatology + spatial adjustment
  - Cross-variable gaps: Spatial PCA
- **Best for**: Optimal performance when gap type is known

## Validation Strategy

### Input Data
- **Original Data**: `../task_1/task1_data/Task1_Combined_Baseline_Daily.csv`
- **Masked Datasets**: `../task_1/masked_datasets/*/` (all 9 gap patterns from Task 1)

### Performance Metrics
- **RMSE** (Root Mean Square Error): Magnitude of errors
- **MAE** (Mean Absolute Error): Average absolute error
- **R²** (Coefficient of Determination): Proportion of variance explained
- **Coverage %**: Percentage of gaps where method is applicable

### Gap Patterns Tested
1. **Random (10%, 20%)**: Uniformly distributed missing values
2. **Block (7-day, 14-day)**: Consecutive missing periods
3. **Seasonal**: Higher missingness during monsoon season
4. **Cross-variable**: Entire variable columns missing
5. **Rolling-origin (4 splits, 90-day)**: Progressive time-based validation
6. **Rolling-origin-180 (4 splits, 180-day)**: Longer test windows

### Validation Considerations
- **Cross-location methods**: Require both locations to have data for training
- **Coverage reporting**: Document percentage of gaps where each method applies
- **Spatial validation**: For cross-location methods, validate on gaps where other location has data

## Results Summary

Results will be compared against Task 2 temporal methods to determine:
1. Where spatial methods outperform temporal methods
2. Best hybrid combinations
3. Variable-specific recommendations
4. Gap-pattern-specific recommendations

### Expected Performance Patterns

**Spatial methods expected to excel**:
- Block gaps (7-day, 14-day): Cross-location provides data when temporal interpolation fails
- Seasonal gaps: Cross-location captures regional patterns
- Edge gaps: Temporal interpolation fails at boundaries
- Variables with strong spatial correlation (SST, wind patterns)

**Temporal methods expected to excel**:
- Random gaps (10%, 20%): Short isolated gaps
- Variables with high temporal autocorrelation (NDVI, CHL)

**Hybrid methods expected to excel**:
- Mixed gap patterns
- Overall robustness across all scenarios

## File Structure
```
task_3/
├── README.md                          # This file
├── run_task3.py                       # Master runner script
├── code/
│   ├── task3_spatial_imputation.py    # Main imputation methods
│   ├── task3_extract_spatial_context.py  # External spatial features
│   └── task3_validation_plots.py      # Visualization suite
└── task3_results/
    ├── spatial_imputation_results.csv     # Detailed per-variable results
    ├── method_comparison_metrics.csv      # Summary by method/mask
    ├── summary_table.csv                  # Overall ranking
    ├── spatial_vs_temporal_comparison.csv # Task 2 vs Task 3
    ├── hybrid_performance.csv             # Best combinations
    └── validation_plots/
        ├── method_comparison_heatmap.png
        ├── variable_performance_boxplot.png
        ├── spatial_correlation_scatter.png
        ├── hybrid_comparison_bar.png
        ├── gap_size_analysis.png
        ├── time_series_examples.png
        └── advection_validation.png
```

## Variables Imputed
All 16 variables from Task 1 & 2:
- **Marine (9)**: CHL, mlotst, no3, o2, po4, so, thetao, uo, vo
- **Atmospheric (7)**: NDVI_daily, NDVI_raw, precip_mm_day, wind_speed_ms, wind_u_ms, wind_v_ms

## Usage Examples

### Run Full Analysis
```bash
cd task_3
python run_task3.py
```

### Run Individual Components
```bash
# Spatial imputation only
python code/task3_spatial_imputation.py

# Generate plots only
python code/task3_validation_plots.py
```

### Custom Method Selection
Edit `task3_spatial_imputation.py` to enable/disable specific methods:
```python
METHODS = {
    'cross_location_regression': True,
    'cross_location_knn': True,
    'distance_weighted': True,
    'spatial_gradient': False,  # Requires external data
    'advection': True,
    'eof_pca': True,
    'kriging': True,
    'dynamic_factor': False,  # Computationally intensive
    'hybrid_sequential': True,
    'hybrid_ensemble': True,
    'hybrid_adaptive': True
}
```

## Key Findings (To Be Updated After Analysis)

### Spatial vs Temporal Comparison
- **Overall winner**: [To be determined]
- **Best spatial method**: [To be determined]
- **Best hybrid method**: [To be determined]

### Variable-Specific Recommendations
- **CHL**: [To be determined]
- **SST (thetao)**: [To be determined]
- **Wind patterns**: [To be determined]
- **NDVI**: [To be determined]

### Gap-Pattern Performance
- **Random gaps**: [To be determined]
- **Block gaps**: [To be determined]
- **Seasonal gaps**: [To be determined]

## Mathematical Formulations

### Cross-Location Correlation
```
ρ(X_Gigantes, X_Roxas) = cov(X_G, X_R) / (σ_G · σ_R)
```

### Spatial Covariance
```
C(d) = E[(Y(x) - μ)(Y(x+d) - μ)]
where d = distance between locations (~60km)
```

### Ensemble Weight Optimization
```
w* = argmin_w Σ(Y_true - (w·Y_temporal + (1-w)·Y_spatial))²
```

## Assumptions and Limitations

### Assumptions
1. **Spatial homogeneity**: Environmental conditions are similar enough between locations for cross-prediction
2. **Stationarity**: Spatial relationships are consistent over time (4-year period)
3. **Independence**: Gaps at different locations are independent (for cross-location methods)
4. **Linear relationships**: Many methods assume linear spatial relationships

### Limitations
1. **Two-site constraint**: Only 2 locations limit spatial interpolation capability
2. **Distance**: 60km separation may be too large for some variables (e.g., coastal-specific features)
3. **No elevation data**: Both sites at sea level, missing topographic effects
4. **Temporal coverage**: 2019-2022 may not capture long-term spatial variability
5. **Aggregated data**: Original grid structure removed during Task 1 processing

### When Spatial Methods May Fail
- **Localized phenomena**: Coastal upwelling, river plumes affecting only one site
- **Differential data quality**: If one location has systematic biases
- **Asynchronous events**: Red tide blooms occurring at different times at each site
- **Instrument-specific gaps**: If gaps are due to sensor failures at specific locations

## Recommendations for Task 4 (XGBoost Feature Engineering)

Based on Task 3 findings, recommended features for XGBoost:

### Spatial Features to Include
1. **Cross-location lags**: X_Roxas(t-1), X_Roxas(t-7) when predicting Gigantes
2. **Spatial differences**: ΔX = X_Gigantes - X_Roxas
3. **Vector magnitudes**: |wind|, |current| from u/v components
4. **EOF modes**: Leading principal components from spatial PCA
5. **Advection lags**: Optimal time lags from advection analysis

### Best Imputation Strategy for Training Data
- Use **[Best Hybrid Method from Task 3]** for pre-processing XGBoost training data
- Document any residual gaps in feature importance analysis
- Consider ensemble of top 3 methods for robustness

## Dependencies
- pandas >= 1.3.0
- numpy >= 1.21.0
- scikit-learn >= 1.0.0
- scipy >= 1.7.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0
- statsmodels >= 0.13.0 (for dynamic factor model)
- pykalman >= 0.9.5 (optional, for Kalman filtering)

## Installation
```bash
pip install pandas numpy scikit-learn scipy matplotlib seaborn statsmodels pykalman
```

## References
- **Kriging**: Cressie, N. (1993). Statistics for Spatial Data. Wiley.
- **EOF Analysis**: Hannachi, A. et al. (2007). Empirical orthogonal functions and related techniques in atmospheric science. International Journal of Climatology.
- **Dynamic Factor Models**: Stock, J. H., & Watson, M. W. (2011). Dynamic factor models. Oxford Handbook of Economic Forecasting.
- **Spatial Interpolation**: Li, J., & Heap, A. D. (2014). Spatial interpolation methods applied in the environmental sciences. Environmental Modelling & Software.

## Notes
- All imputation validated against artificially masked values (known ground truth)
- Results aggregated across 9 gap patterns × 16 variables × 2 locations
- Computational time: ~15-30 minutes for full analysis (varies by method complexity)
- Statistical significance tested via paired t-tests and bootstrap confidence intervals (n=1000)

