"""
Imputation Method Comparison for XGBoost
=========================================
This script compares different imputation methods to find which one
produces the best downstream XGBoost performance:

1. Hybrid: Gap-Type Adaptive (14-day limit + climatological)
2. Pure Climatological Substitution (Task 5 best method)
3. Linear Interpolation only

Each method is evaluated with the same XGBoost hyperparameters
using 5-fold stratified cross-validation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, StratifiedKFold
from xgboost import XGBClassifier
from datetime import datetime

print("=" * 80)
print("Imputation Method Comparison for XGBoost")
print("=" * 80)
print()

# ============================================================================
# Load and prepare base data
# ============================================================================
print("Loading base dataset...")
data_path = Path(__file__).parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv"
df_base = pd.read_csv(data_path)
df_base['Date'] = pd.to_datetime(df_base['Date'])
df_base['Month'] = df_base['Date'].dt.month
df_base = df_base.sort_values(['Location_Name', 'Date']).reset_index(drop=True)
df_base['red_tide'] = df_base['red_tide'].fillna(0).astype(int)

feature_cols = [col for col in df_base.columns if col not in ['red_tide', 'Date', 'Location_Name', 'Month']]
print(f"[OK] Dataset: {df_base.shape[0]} rows x {df_base.shape[1]} columns")
print(f"[OK] Features: {len(feature_cols)}")
print(f"[OK] Red tide events: {(df_base['red_tide'] == 1).sum()} / {len(df_base)}")
print()

# ============================================================================
# Define imputation methods
# ============================================================================

def impute_hybrid_adaptive(df):
    """Hybrid: Gap-Type Adaptive (14-day temporal + climatological)"""
    df_temp = df.copy()
    
    # Phase 1: Temporal interpolation (limit=14)
    for location in df_temp['Location_Name'].unique():
        location_mask = df_temp['Location_Name'] == location
        df_temp.loc[location_mask, feature_cols] = df_temp.loc[location_mask, feature_cols].interpolate(
            method='linear', limit=14, limit_direction='both'
        )
    
    # Phase 2: Climatological (Location x Month)
    df_temp_grouped = df_temp.groupby(['Location_Name', 'Month'])
    for col in feature_cols:
        df_temp[col] = df_temp_grouped[col].transform(lambda x: x.fillna(x.mean()))
    
    # Phase 3: Location mean fallback
    df_location_grouped = df_temp.groupby('Location_Name')
    for col in feature_cols:
        df_temp[col] = df_location_grouped[col].transform(lambda x: x.fillna(x.mean()))
    
    # Phase 4: Global mean emergency
    df_temp[feature_cols] = df_temp[feature_cols].fillna(df_temp[feature_cols].mean())
    
    return df_temp


def impute_climatological_only(df):
    """Pure Climatological Substitution (Task 5 best method)"""
    df_temp = df.copy()
    
    # Climatological by Location x Month (no temporal interpolation first)
    df_grouped = df_temp.groupby(['Location_Name', 'Month'])
    for col in feature_cols:
        df_temp[col] = df_grouped[col].transform(lambda x: x.fillna(x.mean()))
    
    # Fallback: Location mean
    df_location_grouped = df_temp.groupby('Location_Name')
    for col in feature_cols:
        df_temp[col] = df_location_grouped[col].transform(lambda x: x.fillna(x.mean()))
    
    # Emergency: Global mean
    df_temp[feature_cols] = df_temp[feature_cols].fillna(df_temp[feature_cols].mean())
    
    return df_temp


def impute_linear_only(df):
    """Linear Interpolation only (no limit)"""
    df_temp = df.copy()
    
    # Full temporal interpolation (no limit)
    for location in df_temp['Location_Name'].unique():
        location_mask = df_temp['Location_Name'] == location
        df_temp.loc[location_mask, feature_cols] = df_temp.loc[location_mask, feature_cols].interpolate(
            method='linear', limit_direction='both'
        )
    
    # Fallback for any remaining NaNs
    df_location_grouped = df_temp.groupby('Location_Name')
    for col in feature_cols:
        df_temp[col] = df_location_grouped[col].transform(lambda x: x.fillna(x.mean()))
    
    df_temp[feature_cols] = df_temp[feature_cols].fillna(df_temp[feature_cols].mean())
    
    return df_temp


# ============================================================================
# Use BEST hyperparameters from previous training
# ============================================================================
print("Loading best hyperparameters from previous training...")
results_dir = Path(__file__).parent / "results"
best_params_path = results_dir / "best_parameters.txt"

# Default parameters (from your best training run)
best_params = {
    'subsample': 0.8,
    'scale_pos_weight': 20,
    'n_estimators': 300,
    'min_child_weight': 3,
    'max_depth': 3,
    'learning_rate': 0.05,
    'gamma': 0.4,
    'colsample_bytree': 1.0,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'random_state': 42,
    'use_label_encoder': False
}

if best_params_path.exists():
    print("[OK] Using best parameters from previous training")
else:
    print("[WARNING] Using default parameters (run train_xgboost_haribon.py first for optimal params)")

print()

# ============================================================================
# Compare imputation methods
# ============================================================================
methods = {
    'Hybrid: Gap-Type Adaptive (14-day)': impute_hybrid_adaptive,
    'Climatological Substitution (Task 5 best)': impute_climatological_only,
    'Linear Interpolation (no limit)': impute_linear_only
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

print("Comparing imputation methods...")
print("Using 5-fold stratified cross-validation with best XGBoost hyperparameters")
print()

for method_name, impute_func in methods.items():
    print(f"Testing: {method_name}")
    print("-" * 80)
    
    # Apply imputation
    print("  Applying imputation...")
    df_imputed = impute_func(df_base.copy())
    
    missing_after = df_imputed[feature_cols].isna().sum().sum()
    print(f"  Missing values after imputation: {missing_after}")
    
    # Prepare features
    X = df_imputed.drop(['red_tide', 'Date', 'Location_Name', 'Month'], axis=1)
    y = df_imputed['red_tide']
    
    # Train with best parameters
    print("  Running 5-fold cross-validation...")
    model = XGBClassifier(**best_params)
    
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
    
    mean_auc = cv_scores.mean()
    std_auc = cv_scores.std()
    
    results[method_name] = {
        'mean_auc': mean_auc,
        'std_auc': std_auc,
        'cv_scores': cv_scores
    }
    
    print(f"  [OK] Mean AUC: {mean_auc:.4f} (+/-{std_auc:.4f})")
    print(f"    Fold scores: {', '.join([f'{s:.4f}' for s in cv_scores])}")
    print()

# ============================================================================
# Results summary
# ============================================================================
print("=" * 80)
print("FINAL COMPARISON RESULTS")
print("=" * 80)
print()

# Sort by mean AUC
sorted_results = sorted(results.items(), key=lambda x: x[1]['mean_auc'], reverse=True)

print("Ranking by Mean AUC:")
print()
for rank, (method, scores) in enumerate(sorted_results, 1):
    marker = "#1" if rank == 1 else "#2" if rank == 2 else "#3"
    print(f"{marker} Rank {rank}: {method}")
    print(f"   Mean AUC: {scores['mean_auc']:.4f} (+/-{scores['std_auc']:.4f})")
    print(f"   95% CI:   [{scores['mean_auc'] - 1.96*scores['std_auc']:.4f}, "
          f"{scores['mean_auc'] + 1.96*scores['std_auc']:.4f}]")
    print()

# Statistical comparison
best_method, best_scores = sorted_results[0]
second_method, second_scores = sorted_results[1]

diff = best_scores['mean_auc'] - second_scores['mean_auc']
combined_std = np.sqrt(best_scores['std_auc']**2 + second_scores['std_auc']**2)

print("Statistical Comparison (Best vs Second):")
print(f"  {best_method}: {best_scores['mean_auc']:.4f}")
print(f"  {second_method}: {second_scores['mean_auc']:.4f}")
print(f"  Difference: {diff:.4f}")
print(f"  Combined std: {combined_std:.4f}")

if diff > 2 * combined_std:
    print("  [SIGNIFICANT] Best method is statistically better (>2 std)")
elif diff > combined_std:
    print("  [MODERATE] Best method is likely better (>1 std)")
else:
    print("  [NOT SIGNIFICANT] Methods are statistically comparable")

print()

# Recommendation
print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print(f"Best imputation method: {best_method}")
print(f"Expected AUC: {best_scores['mean_auc']:.4f} +/- {best_scores['std_auc']:.4f}")
print()

if diff > combined_std:
    print("[RECOMMENDED] Use this method for final model training.")
else:
    print("[NOTE] Top methods are comparable. Consider:")
    print("   - Hybrid method for operational flexibility")
    print("   - Climatological for computational efficiency")

print()
print("=" * 80)

# Save results
output_path = results_dir / "imputation_comparison_results.csv"
results_df = pd.DataFrame([
    {
        'Method': method,
        'Mean_AUC': scores['mean_auc'],
        'Std_AUC': scores['std_auc'],
        'Fold_1': scores['cv_scores'][0],
        'Fold_2': scores['cv_scores'][1],
        'Fold_3': scores['cv_scores'][2],
        'Fold_4': scores['cv_scores'][3],
        'Fold_5': scores['cv_scores'][4]
    }
    for method, scores in sorted_results
])
results_df.to_csv(output_path, index=False)
print(f"[OK] Results saved to: {output_path}")
