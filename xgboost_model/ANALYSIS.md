# XGBoost Red Tide Prediction Model

**Dataset:** Combined_Labeled.csv (7 locations, 2015-2026)  
**Model:** XGBoost with Hybrid Gap-Type Adaptive Imputation  
**Evaluation:** Six expanding temporal test windows  
**Metrics:** Accuracy, Precision, Recall, F1-Score, AUC-ROC  
**Date:** April 2026

---

## Overview

This model predicts red tide blooms using XGBoost trained on daily observations from 7 monitoring sites with environmental features such as CHL, NDVI, SST, salinity, currents, wind, and precipitation.

The evaluation was updated from the old 5-fold random cross-validation setup to a time-aware expanding-window protocol. This gives a more realistic estimate of forecasting performance because each test set is strictly in the future relative to the training set.

**Updated pipeline:**
1. Load and filter data, keeping only rows with `red_tide_label`
2. Convert `red_tide_label` to binary using threshold >= 0.5
3. Apply Hybrid Gap-Type Adaptive imputation inside each split
4. Train XGBoost on the expanding training window
5. Evaluate on the next one-year test window
6. Report Accuracy, Precision, Recall, F1-Score, AUC-ROC, and training runtime
7. Save per-split metrics, summary metrics, and the final model

---

## Data Preparation

### Dataset
- **Source:** `final_compiled_dataset/Combined_Labeled.csv`
- **Temporal range:** 2015-01-01 to 2026-02-24
- **Locations:** 7 sites
- **Target rows used:** rows with non-missing `red_tide_label`
- **Features:** environmental variables excluding Date, Location_Name, Month, red_tide, red_tide_label, and red_tide_binary

### Target Variable

- **Column:** `red_tide_label` (continuous float 0.0-1.0)
- **Binary conversion:** `red_tide_label >= 0.5` -> 1 (bloom), else 0 (non-bloom)
- **Class imbalance:** the non-bloom class remains the majority class, so `scale_pos_weight` is preserved in the tuned XGBoost parameters

### Preprocessing Steps

1. Drop rows where `red_tide_label` is missing
2. Convert `red_tide_label` to `red_tide_binary`
3. Sort chronologically by `Location_Name` and `Date`
4. Extract `Month` for climatological imputation

---

## Imputation Methodology

### Hybrid: Gap-Type Adaptive Strategy

The imputation logic is applied within each split to avoid using future information from the test period.

**Phase 1: Temporal Interpolation**
- Method: Linear interpolation within each location
- Limit: 14 days
- Purpose: Fill short gaps using local continuity

**Phase 2: Climatological Substitution**
- Method: Location x Month mean substitution
- Purpose: Preserve seasonal structure when interpolation is insufficient

**Phase 3: Location Mean Fallback**
- Method: Overall mean per location
- Purpose: Handle edge cases where month-level statistics are still missing

**Phase 4: Global Mean Emergency Fallback**
- Method: Overall feature mean
- Purpose: Fill any remaining rare gaps

For the expanding-window evaluation, the imputer statistics are learned from the training portion of each split and then applied to the corresponding test period.

---

## Temporal Evaluation Setup

### Six Expanding Windows

The model is evaluated using the following train/test windows:

1. **Split 1**
   - Train: 2015-2019
   - Test: 2020

2. **Split 2**
   - Train: 2015-2020
   - Test: 2021

3. **Split 3**
   - Train: 2015-2021
   - Test: 2022

4. **Split 4**
   - Train: 2015-2022
   - Test: 2023

5. **Split 5**
   - Train: 2015-2023
   - Test: 2024

6. **Split 6**
   - Train: 2015-2024
   - Test: 2025

All six splits use strict one-year test windows (Jan 1 to Dec 31).

### Why this is better

- It prevents future leakage from random folds.
- It better reflects operational forecasting conditions.
- It produces a more defensible thesis result even if the raw metric values are lower than the older random CV score.

---

## Model Training

### XGBoost Configuration

The model uses the best hyperparameters found in the earlier tuning run and reuses them for the six-window evaluation.

**Best parameters used in the current script:**
- `subsample: 0.9`
- `scale_pos_weight: 5`
- `n_estimators: 500`
- `min_child_weight: 7`
- `max_depth: 8`
- `learning_rate: 0.2`
- `gamma: 0.2`
- `colsample_bytree: 0.9`

### Metrics Reported

For each split, the script reports:
- Accuracy
- Precision
- Recall
- F1-Score
- AUC-ROC
- Training runtime in seconds

It also saves the mean, standard deviation, minimum, and maximum for each metric across the six splits.

---

## Expected Result Pattern

Because the new evaluation is time-based, the reported scores are expected to be more realistic than the old random-fold AUC score.

What usually changes compared with the old setup:
- The AUC may go down slightly because the test set is now truly future data.
- Precision and recall may vary more across splits because bloom events are not evenly distributed by year.
- Runtime becomes more visible because the script now tracks fit time for each split.

This is not a weaker evaluation. It is a stricter and more credible one.

---

## Output Files

The updated script saves the following files in `xgboost_model/results/`:
- `temporal_window_results.csv` - per-split metrics and training runtime
- `temporal_window_summary.csv` - aggregated statistics across the six splits
- `temporal_window_summary.txt` - human-readable summary for documentation
- `best_xgboost_model.json` - final model trained after the evaluation run
- `best_parameters.txt` - tuned parameter summary and aggregate metrics

---

## Usage

To run the updated training and evaluation workflow:

```bash
python xgboost_model/train_xgboost_haribon.py
```

To load the final trained model:

```python
from xgboost import XGBClassifier

model = XGBClassifier()
model.load_model('xgboost_model/results/best_xgboost_model.json')
```

---

## Summary

The main difference from the original XGBoost workflow is that the model is no longer evaluated with 5-fold random cross-validation and AUC only. It now uses six expanding temporal test windows, four standard classification metrics plus AUC-ROC, and explicit training runtime reporting. This makes the result more appropriate for a forecasting thesis and less vulnerable to leakage.

**Last Updated:** April 21, 2026
