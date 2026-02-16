# HARIBON Red Tide Validation Study - Task 2: Temporal Imputation Methods

## Overview
Task 2 implements and validates temporal imputation methods for handling missing data in environmental time series. The focus is on time-based imputation techniques that leverage temporal patterns in the data.

## Quick Start

### Run Complete Task 2 Analysis
```bash
cd task_2
python run_task2.py
```

This will execute both the imputation analysis and generate all validation plots.

### Individual Steps
```bash
# Step 1: Run imputation analysis
python code/task2_temporal_imputation.py

# Step 2: Generate validation plots
python code/task2_validation_plots.py
```

## Imputation Methods Implemented

### 1. Linear Interpolation
- **Description**: Uses linear interpolation between known values to fill gaps
- **Best for**: Short gaps where the relationship is approximately linear
- **Implementation**: `pandas.DataFrame.interpolate(method='linear')`

### 2. Climatological Substitution
- **Description**: Replaces missing values with the long-term average for that day-of-year across all available years
- **Best for**: Seasonal/cyclical data with strong annual patterns
- **Implementation**: Computes day-of-year averages from baseline data

## Validation Strategy

### Input Data
- **Original Data**: `../task_1/task1_data/Task1_Combined_Baseline_Daily.csv`
- **Masked Datasets**: `../task_1/masked_datasets/*/` (artificially gapped data from Task 1)

### Performance Metrics
- **RMSE** (Root Mean Square Error): Measures magnitude of errors
- **MAE** (Mean Absolute Error): Measures average absolute error
- **R²** (Coefficient of Determination): Measures proportion of variance explained

### Gap Patterns Tested
1. **Random (10%, 20%)**: Uniformly distributed missing values
2. **Block (7-day, 14-day)**: Consecutive missing periods
3. **Seasonal**: Higher missingness during monsoon season
4. **Cross-variable**: Entire variable columns missing
5. **Rolling-origin**: Time-based train/test splits

## Results Summary

Based on the analysis of all gap patterns and variables:

### Overall Performance
- **Linear Interpolation**: Generally better for most scenarios
  - Lower RMSE and MAE across most gap patterns
  - Better R² scores for random and block gaps
- **Climatological Substitution**: Better for some seasonal variables
  - Performs well for NDVI and precipitation
  - Can struggle with variables having high temporal variability

### Performance by Gap Pattern
1. **Random gaps (10%, 20%)**: Linear interpolation performs best
2. **Block gaps (7-day, 14-day)**: Linear interpolation superior for shorter gaps
3. **Seasonal gaps**: Mixed performance, depends on variable
4. **Cross-variable gaps**: Both methods perform well

### Variable-Specific Insights
- **Marine variables** (CHL, nutrients): Linear interpolation typically better
- **Atmospheric variables** (NDVI, precipitation): Climatological substitution can be competitive
- **Wind variables**: Linear interpolation generally superior

## File Structure
```
task_2/
├── code/
│   ├── task2_temporal_imputation.py    # Main imputation script
│   └── task2_validation_plots.py       # Visualization script
└── task2_results/
    ├── temporal_imputation_results.csv # Detailed results
    ├── method_comparison_metrics.csv   # Summary metrics
    ├── summary_table.csv              # Overall summary
    └── validation_plots/
        ├── method_comparison.png
        ├── variable_performance.png
        ├── error_distributions.png
        └── performance_heatmap.png
```

## Variables Imputed
- **Marine**: CHL, mlotst, no3, o2, po4, so, thetao, uo, vo
- **Atmospheric**: NDVI_daily, NDVI_raw, precip_mm_day, wind_speed_ms, wind_u_ms, wind_v_ms

## Usage

### Run Imputation Analysis
```bash
cd task_2/code
python task2_temporal_imputation.py
```

### Generate Validation Plots
```bash
python task2_validation_plots.py
```

## Key Findings

### Expected Performance Patterns
1. **Linear Interpolation** typically performs better for:
   - Short gaps (block_7day)
   - Variables with smooth temporal trends
   - Marine variables with gradual changes

2. **Climatological Substitution** typically performs better for:
   - Seasonal variables (NDVI, precipitation)
   - Long gaps (block_14day, seasonal)
   - Variables with strong annual cycles

### Variable-Specific Insights
- **Marine variables** (CHL, nutrients): Linear interpolation often superior
- **Atmospheric variables** (precipitation, wind): Climatological substitution may work better
- **NDVI**: Seasonal patterns favor climatological approach

## Next Steps
- Results from Task 2 will be compared with spatial imputation methods in Task 3
- Best performing temporal methods will be used in Task 4 for XGBoost baseline training
- Final recommendations will be compiled in Task 5

## Dependencies
- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn

## Notes
- All imputation is performed independently per location and variable
- Validation uses only artificially masked values (known ground truth)
- Results are aggregated across all gap patterns and variables for comprehensive evaluation