# XGBoost Red Tide Prediction Notebook Analysis

**Notebook:** `xgboost_model/xgboost_training.ipynb`  
**Dataset:** `final_compiled_dataset/Combined_Labeled.csv`  
**Model:** XGBoost (binary classification)  
**Evaluation:** 6 temporal splits (rolling-origin style)  
**Metrics:** Accuracy, Precision, Recall, F1, AUC  
**Date:** April 2026

---

## Overview

This notebook predicts red tide risk from multi-source environmental features using XGBoost. The pipeline includes data loading, hybrid gap-adaptive imputation, label binarization, temporal split evaluation, and aggregate reporting.

Notebook flow:
1. Load and inspect data
2. Impute missing values with gap-length-based strategy
3. Binarize `red_tide_label` using threshold 0.5
4. Evaluate by temporal splits
5. Tune XGBoost per split with `RandomizedSearchCV`
6. Save per-split results to CSV and print aggregate metrics

---

## Data and Features

- Source file: `Combined_Labeled.csv`
- Rows are sorted by `Location_Name` and `Date`
- Target column: `red_tide_label`
- Binary target used for training: `target = (red_tide_label >= 0.5).astype(int)`

Features used in the notebook:
- `CHL`
- `NDVI_daily`
- `mlotst`
- `precip_mm_day`
- `so`
- `thetao`
- `uo`
- `vo`
- `wind_speed_ms`
- `wind_u_ms`
- `wind_v_ms`

---

## Imputation in Notebook

The notebook applies a hybrid gap-adaptive imputation before model training:
- Gap < 7 days: linear interpolation
- Gap 7-30 days: polynomial interpolation (order 2)
- Gap > 30 days: climatological mean by month-day within location
- Final fill: forward fill then backward fill

---

## Temporal Split Setup

The notebook defines these splits:
1. Train <= 2019, Test = [2020]
2. Train <= 2020, Test = [2021]
3. Train <= 2021, Test = [2022]
4. Train <= 2022, Test = [2023]
5. Train <= 2023, Test = [2024]
6. Train <= 2024, Test = [2025, 2026]

Note: the final split uses a two-year test window.

---

## XGBoost Tuning Setup

Per split, the notebook runs `RandomizedSearchCV` with:
- Estimator: `XGBClassifier(objective='binary:logistic', eval_metric='auc', random_state=42)`
- `n_iter=20`
- `cv=3`
- `scoring='roc_auc'`
- `n_jobs=-1`

Search space:
- `learning_rate`: [0.01, 0.05, 0.1, 0.2]
- `max_depth`: [3, 4, 5, 6, 7, 8]
- `n_estimators`: [50, 100, 200, 300, 500]
- `subsample`: [0.6, 0.7, 0.8, 0.9, 1.0]
- `colsample_bytree`: [0.6, 0.7, 0.8, 0.9, 1.0]
- `scale_pos_weight`: [1, 5, 10, 20, 50, 100]
- `min_child_weight`: [1, 3, 5, 7]
- `gamma`: [0, 0.1, 0.2, 0.3, 0.4]

---

## Metrics and Output

For each split, the notebook computes:
- Accuracy
- Precision
- Recall
- F1
- AUC

The notebook then:
- Builds `results_df` from split-level outputs
- Prints aggregate mean +- std for key metrics
- Saves results to: `xgboost_model/results/xgboost_split_metrics.csv`

---

## Notes for Consistency

- This analysis reflects the notebook implementation, not the separate script-based pipeline.
- If notebook outputs and script outputs differ, use notebook outputs as the source of truth when reporting notebook results.

---

## Summary

The notebook implements split-wise hyperparameter tuning and evaluation over six temporal splits, with the final split testing on 2025-2026. Final reported outputs are split-level and aggregate metrics stored in `xgboost_split_metrics.csv`.

**Last Updated:** April 23, 2026
