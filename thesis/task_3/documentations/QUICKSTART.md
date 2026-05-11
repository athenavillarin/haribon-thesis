# Task 3: Quick Start Guide

## Prerequisites Check

Before running Task 3, ensure:

```bash
# 1. Verify Task 1 data exists
Test-Path ..\task_1\task1_data\Task1_Combined_Baseline_Daily.csv

# 2. Verify masked datasets exist
Test-Path ..\task_1\masked_datasets\random_10\masked_data.csv

# 3. Check Python packages
python -c "import pandas, numpy, sklearn, scipy, matplotlib, seaborn; print('✓ All packages installed')"
```

## Run Task 3 (Complete Analysis)

```bash
# Navigate to task_3 directory
cd task_3

# Run everything (15-30 minutes)
python run_task3.py
```

## What Will Happen

### Stage 1: Spatial Imputation (10-20 minutes)
- Loads baseline data and 11 masked datasets
- Applies 9 imputation methods
- Processes 16 variables × 2 locations
- Validates against ground truth
- Saves results to `task3_results/spatial_imputation_results.csv`

Progress output:
```
Processing: random_10
  Method: Cross-Location Linear Regression
    [  2.1%] CHL @ Gigantes... RMSE: 0.856
    [  2.3%] CHL @ Roxas... RMSE: 0.921
    ...
```

### Stage 2: Validation Plots (2-5 minutes)
- Generates 7 publication-quality plots
- Saves to `task3_results/validation_plots/`

## Verify Results

**Check CSV results:**
```bash
# Should have ~2,300 rows
(Import-Csv task3_results\spatial_imputation_results.csv).Count

# View summary
Import-Csv task3_results\summary_table.csv | Format-Table
```

**Check plots:**
```bash
# Should have 7 PNG files
Get-ChildItem task3_results\validation_plots\*.png | Select-Object Name
```

Expected files:
- method_comparison_heatmap.png
- variable_performance_boxplot.png
- spatial_correlation_scatter.png
- hybrid_comparison_bar.png
- gap_size_analysis.png
- time_series_example.png
- method_ranking.png

## Interpret Results

### 1. Best Overall Method
```bash
# View method ranking
Import-Csv task3_results\summary_table.csv | 
  Sort-Object rmse | 
  Select-Object -First 3 method_name, rmse, mae, r2
```

### 2. Best by Gap Pattern
```bash
# View method comparison
Import-Csv task3_results\method_comparison_metrics.csv | 
  Where-Object mask_type -eq 'block_7day' |
  Sort-Object rmse_mean
```

### 3. Spatial vs Temporal Comparison
```bash
# Compare with Task 2 results
Import-Csv task3_results\spatial_vs_temporal_comparison.csv
```

## Next Steps

### For Thesis Analysis
1. Open validation plots in `validation_plots/`
2. Examine `summary_table.csv` for key findings
3. Compare with Task 2 results
4. Document insights in thesis chapters

### For Task 4 (XGBoost)
Use the best performing method from `summary_table.csv` to preprocess data:
- Likely: Hybrid Sequential or Hybrid Ensemble
- Apply to full dataset before XGBoost training
- Include spatial features (cross-location lags, EOF modes)

## Troubleshooting

**"File not found" error:**
```bash
# Verify you're in task_3 directory
$PWD.Path

# Should show: C:\Users\...\haribon-thesis\task_3
# If not: cd C:\Users\meagie\Desktop\haribon-thesis\task_3
```

**"Module not found" error:**
```bash
# Install missing packages
pip install pandas numpy scikit-learn scipy matplotlib seaborn statsmodels
```

**Memory error:**
Edit `task3_spatial_imputation.py` line ~950:
```python
# Process fewer datasets at once
datasets = datasets[:3]  # Test with first 3 datasets only
```

**Long runtime:**
This is normal! Full analysis takes 15-30 minutes. Monitor progress percentage.

## Optional: Extract Spatial Features

**Note:** Main spatial imputation works WITHOUT this step.

This is for advanced users who want to add spatial gradient features:

```bash
python code/task3_extract_spatial_context.py
```

This generates synthetic spatial features (variance, gradients) that could be integrated into Method 4 (Spatial Gradient Model).

## Quick Test (Debug Mode)

To test before full run:

```python
# Edit task3_spatial_imputation.py
# Line ~950, change:
datasets = discover_masked_datasets()

# To:
datasets = [('random_10', None)]  # Test on 1 dataset only

# Line ~26, change:
METHODS = {
    'cross_location_regression': 'Cross-Location Linear Regression',
    # ... comment out other methods
}

# To test just one method
```

Then run:
```bash
python code/task3_spatial_imputation.py
```

Should complete in ~2-3 minutes.

## Success Indicators

✓ No error messages in terminal  
✓ `spatial_imputation_results.csv` has ~2,300 rows  
✓ All 7 plots generated  
✓ RMSE values are positive and reasonable (<10)  
✓ R² values are between -∞ and 1.0  
✓ Hybrid methods show competitive RMSE  

## Time Estimates

| Task | Time | Output |
|------|------|--------|
| Spatial imputation | 10-20 min | results CSV |
| Validation plots | 2-5 min | 7 PNG files |
| Total | **15-30 min** | Complete analysis |

## Need Help?

1. Check IMPLEMENTATION_SUMMARY.md for detailed troubleshooting
2. Review README.md for method descriptions
3. Examine code comments in task3_spatial_imputation.py
4. Verify Task 1 completed successfully

---

**Ready to run? Execute:**
```bash
cd task_3
python run_task3.py
```
