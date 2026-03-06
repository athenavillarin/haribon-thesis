"""
XGBoost Model Training with HARIBON Methodology
================================================
This script implements:
1. Data preparation from Combined_Labeled.csv
2. Hybrid: Gap-Type Adaptive imputation (14-day temporal limit + climatological fallback)
3. XGBoost hyperparameter optimization using RandomizedSearchCV
4. Cross-validation with stratified folding for imbalanced red tide events
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from xgboost import XGBClassifier
from datetime import datetime

print("=" * 80)
print("XGBoost Model Training with HARIBON Methodology")
print("=" * 80)
print()

# ============================================================================
# Step 1: Data Preparation
# ============================================================================
print("Step 1: Loading and preparing data...")

# Load dataset
data_path = Path(__file__).parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv"
df = pd.read_csv(data_path)
print(f"[OK] Loaded dataset: {df.shape[0]} rows x {df.shape[1]} columns")

# Convert Date to datetime and extract Month
df['Date'] = pd.to_datetime(df['Date'])
df['Month'] = df['Date'].dt.month
print(f"[OK] Extracted Month from Date column")

# Sort chronologically by Location and Date
df = df.sort_values(['Location_Name', 'Date']).reset_index(drop=True)
print(f"[OK] Sorted by Location_Name and Date")

# Drop rows where red_tide_label is unavailable (required for supervised training)
before_drop = len(df)
df = df.dropna(subset=['red_tide_label']).reset_index(drop=True)
print(f"[OK] Dropped {before_drop - len(df)} rows with missing red_tide_label ({len(df)} rows remaining)")

# Binary conversion: red_tide_label >= 0.5 → 1 (bloom), else 0
df['red_tide_binary'] = (df['red_tide_label'] >= 0.5).astype(int)
print(f"[OK] Binarized red_tide_label using threshold=0.5")
print(f"  Binary class distribution: {df['red_tide_binary'].value_counts().to_dict()}")
print()

# ============================================================================
# Step 2: Hybrid: Gap-Type Adaptive Imputation
# ============================================================================
print("Step 2: Applying Hybrid: Gap-Type Adaptive imputation...")

# Identify feature columns (exclude target columns, Date, Location, Month)
feature_cols = [col for col in df.columns if col not in ['red_tide', 'red_tide_label', 'red_tide_binary', 'Date', 'Location_Name', 'Month']]
print(f"  Feature columns to impute: {len(feature_cols)}")
print(f"  Features: {', '.join(feature_cols[:5])}..." if len(feature_cols) > 5 else f"  Features: {', '.join(feature_cols)}")

# Track missing values before imputation
missing_before = df[feature_cols].isna().sum().sum()
print(f"  Missing values before imputation: {missing_before:,}")

# Phase 1: Short Gaps - Temporal Linear Interpolation (limit=14 days)
print("  Phase 1: Temporal interpolation (limit=14 days)...")
df_temp = df.copy()
for location in df_temp['Location_Name'].unique():
    location_mask = df_temp['Location_Name'] == location
    df_temp.loc[location_mask, feature_cols] = df_temp.loc[location_mask, feature_cols].interpolate(
        method='linear',
        limit=14,
        limit_direction='both'
    )

missing_after_phase1 = df_temp[feature_cols].isna().sum().sum()
imputed_phase1 = missing_before - missing_after_phase1
print(f"    [OK] Imputed {imputed_phase1:,} values using temporal interpolation")

# Phase 2: Long Gaps - Climatological Substitution (by Location + Month)
print("  Phase 2: Climatological substitution (by Location x Month)...")
df_temp_grouped = df_temp.groupby(['Location_Name', 'Month'])
for col in feature_cols:
    df_temp[col] = df_temp_grouped[col].transform(lambda x: x.fillna(x.mean()))

missing_after_phase2 = df_temp[feature_cols].isna().sum().sum()
imputed_phase2 = missing_after_phase1 - missing_after_phase2
print(f"    [OK] Imputed {imputed_phase2:,} values using climatological means")

# Phase 3: Fallback - Overall Location Mean
print("  Phase 3: Fallback (overall Location mean)...")
df_location_grouped = df_temp.groupby('Location_Name')
for col in feature_cols:
    df_temp[col] = df_location_grouped[col].transform(lambda x: x.fillna(x.mean()))

missing_after_phase3 = df_temp[feature_cols].isna().sum().sum()
imputed_phase3 = missing_after_phase2 - missing_after_phase3
print(f"    [OK] Imputed {imputed_phase3:,} values using location means")

# Final check: if any NaNs remain, fill with global mean (emergency fallback)
if df_temp[feature_cols].isna().sum().sum() > 0:
    print("  Phase 4: Emergency fallback (global mean for any remaining NaNs)...")
    df_temp[feature_cols] = df_temp[feature_cols].fillna(df_temp[feature_cols].mean())
    print(f"    [OK] Applied global mean to remaining NaNs")

df = df_temp
missing_after = df[feature_cols].isna().sum().sum()
print(f"  Missing values after imputation: {missing_after:,}")
print(f"  [OK] Total imputed: {missing_before - missing_after:,} values")
print()

# ============================================================================
# Step 3: Model Setup
# ============================================================================
print("Step 3: Preparing features and target...")

# Define X and y
X = df.drop(['red_tide', 'red_tide_label', 'red_tide_binary', 'Date', 'Location_Name', 'Month'], axis=1)
y = df['red_tide_binary']

print(f"[OK] X shape: {X.shape}")
print(f"[OK] y shape: {y.shape}")
print(f"[OK] Feature columns: {list(X.columns)}")
print(f"[OK] Class distribution (binary, threshold=0.5): {y.value_counts().to_dict()}")
print(f"[OK] Class imbalance ratio: {(y == 0).sum() / (y == 1).sum():.2f}:1 (non-bloom:bloom)")
print()

# ============================================================================
# Step 4: XGBoost Hyperparameter Optimization
# ============================================================================
print("Step 4: XGBoost hyperparameter optimization...")
print("  Using RandomizedSearchCV with StratifiedKFold (n_splits=5)")
print()

# Initialize XGBoost classifier
xgb_model = XGBClassifier(
    objective='binary:logistic',
    eval_metric='auc',
    random_state=42
)

# Hyperparameter search grid
param_grid = {
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'max_depth': [3, 4, 5, 6, 7, 8],
    'n_estimators': [50, 100, 200, 300, 500],
    'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
    'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
    'scale_pos_weight': [1, 5, 10, 20, 50, 100],  # Handle class imbalance
    'min_child_weight': [1, 3, 5, 7],
    'gamma': [0, 0.1, 0.2, 0.3, 0.4]
}

print("  Hyperparameter search space:")
for param, values in param_grid.items():
    print(f"    {param}: {values}")
print()

# Stratified K-Fold cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# RandomizedSearchCV
print("  Starting RandomizedSearchCV (n_iter=50, scoring='roc_auc')...")
print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

random_search = RandomizedSearchCV(
    estimator=xgb_model,
    param_distributions=param_grid,
    n_iter=50,
    scoring='roc_auc',
    cv=cv,
    verbose=2,
    random_state=42,
    n_jobs=-1  # Use all available cores
)

# Fit the search
random_search.fit(X, y)

# ============================================================================
# Results
# ============================================================================
print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()
print(f"Best Cross-Validation AUC Score: {random_search.best_score_:.4f}")
print()
print("Best Hyperparameters:")
for param, value in random_search.best_params_.items():
    print(f"  {param}: {value}")
print()

# Additional statistics
cv_results = pd.DataFrame(random_search.cv_results_)
print("Top 5 Configurations by AUC:")
top_5 = cv_results.nlargest(5, 'mean_test_score')[['mean_test_score', 'std_test_score', 'rank_test_score']]
for idx, row in top_5.iterrows():
    print(f"  Rank {int(row['rank_test_score'])}: AUC = {row['mean_test_score']:.4f} (+/-{row['std_test_score']:.4f})")
print()

# Save results
output_dir = Path(__file__).parent / "results"
output_dir.mkdir(exist_ok=True)

# Save best model
best_model = random_search.best_estimator_
model_path = output_dir / "best_xgboost_model.json"
best_model.save_model(model_path)
print(f"[OK] Best model saved to: {model_path}")

# Save CV results
cv_results_path = output_dir / "cv_results.csv"
cv_results.to_csv(cv_results_path, index=False)
print(f"[OK] CV results saved to: {cv_results_path}")

# Save best parameters
best_params_path = output_dir / "best_parameters.txt"
with open(best_params_path, 'w') as f:
    f.write("XGBoost Best Hyperparameters\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Best Cross-Validation AUC: {random_search.best_score_:.4f}\n\n")
    f.write("Best Parameters:\n")
    for param, value in random_search.best_params_.items():
        f.write(f"  {param}: {value}\n")
print(f"[OK] Best parameters saved to: {best_params_path}")

print()
print("=" * 80)
print("Training completed successfully!")
print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
