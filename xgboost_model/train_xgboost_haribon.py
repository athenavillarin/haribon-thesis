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

<<<<<<< Updated upstream
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
=======
SPLITS = [
    {
        'name': 'Split 1',
        'train_start': '2015-01-01',
        'train_end': '2019-12-31',
        'test_start': '2020-01-01',
        'test_end': '2020-12-31',
    },
    {
        'name': 'Split 2',
        'train_start': '2015-01-01',
        'train_end': '2020-12-31',
        'test_start': '2021-01-01',
        'test_end': '2021-12-31',
    },
    {
        'name': 'Split 3',
        'train_start': '2015-01-01',
        'train_end': '2021-12-31',
        'test_start': '2022-01-01',
        'test_end': '2022-12-31',
    },
    {
        'name': 'Split 4',
        'train_start': '2015-01-01',
        'train_end': '2022-12-31',
        'test_start': '2023-01-01',
        'test_end': '2023-12-31',
    },
    {
        'name': 'Split 5',
        'train_start': '2015-01-01',
        'train_end': '2023-12-31',
        'test_start': '2024-01-01',
        'test_end': '2024-12-31',
    },
    {
        'name': 'Split 6',
        'train_start': '2015-01-01',
        'train_end': '2024-12-31',
        'test_start': '2025-01-01',
        'test_end': '2025-12-31',
    },
]


def print_header() -> None:
    print("=" * 80)
    print("XGBoost Model Training with HARIBON Methodology")
    print("=" * 80)
    print()


def validate_splits_one_year(splits: list[dict]) -> None:
    for split in splits:
        if split.get('test_end') is None:
            raise ValueError(f"{split['name']} must define test_end for strict 1-year evaluation.")

        test_start = pd.Timestamp(split['test_start'])
        test_end = pd.Timestamp(split['test_end'])

        if test_start.year != test_end.year:
            raise ValueError(
                f"{split['name']} test window spans multiple years: {test_start.date()} to {test_end.date()}"
            )

        if test_start.month != 1 or test_start.day != 1 or test_end.month != 12 or test_end.day != 31:
            raise ValueError(
                f"{split['name']} must be full calendar year (Jan 1 to Dec 31), got {test_start.date()} to {test_end.date()}"
            )


def load_best_params(best_params_path: Path) -> dict:
    if not best_params_path.exists():
        return DEFAULT_BEST_PARAMS.copy()

    params = DEFAULT_BEST_PARAMS.copy()
    param_pattern = re.compile(r"^\s*([a-z_]+):\s+([-+]?[0-9]*\.?[0-9]+)\s*$")

    with open(best_params_path, 'r', encoding='utf-8') as handle:
        for line in handle:
            match = param_pattern.match(line)
            if not match:
                continue

            key = match.group(1)
            raw_value = match.group(2)
            value = float(raw_value) if '.' in raw_value else int(raw_value)
            params[key] = value

    return params


def prepare_data(data_path: Path) -> tuple[pd.DataFrame, list[str]]:
    print("Step 1: Loading and preparing data...")
    df = pd.read_csv(data_path)
    print(f"[OK] Loaded dataset: {df.shape[0]} rows x {df.shape[1]} columns")

    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.month
    print("[OK] Extracted Month from Date column")

    df = df.sort_values(['Location_Name', 'Date']).reset_index(drop=True)
    print("[OK] Sorted by Location_Name and Date")

    before_drop = len(df)
    df = df.dropna(subset=['red_tide_label']).reset_index(drop=True)
    print(f"[OK] Dropped {before_drop - len(df)} rows with missing red_tide_label ({len(df)} rows remaining)")

    df['red_tide_binary'] = (df['red_tide_label'] >= 0.5).astype(int)
    print("[OK] Binarized red_tide_label using threshold=0.5")
    print(f"  Binary class distribution: {df['red_tide_binary'].value_counts().to_dict()}")
    print()

    feature_cols = [
        col
        for col in df.columns
        if col not in ['red_tide', 'red_tide_label', 'red_tide_binary', 'Date', 'Location_Name', 'Month']
    ]
    return df, feature_cols


def interpolate_within_location(df_subset: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    df_temp = df_subset.sort_values(['Location_Name', 'Date']).reset_index(drop=True).copy()
    for location in df_temp['Location_Name'].unique():
        location_mask = df_temp['Location_Name'] == location
        df_temp.loc[location_mask, feature_cols] = df_temp.loc[location_mask, feature_cols].interpolate(
            method='linear',
            limit=14,
            limit_direction='both'
        )
    return df_temp


def build_imputer_stats(df_temp: pd.DataFrame, feature_cols: list[str]) -> dict:
    month_means = df_temp.groupby(['Location_Name', 'Month'])[feature_cols].mean()
    location_means = df_temp.groupby('Location_Name')[feature_cols].mean()
    global_means = df_temp[feature_cols].mean()

    return {
        'month_lookup': {col: month_means[col].to_dict() for col in feature_cols},
        'location_lookup': {col: location_means[col].to_dict() for col in feature_cols},
        'global_means': global_means,
    }


def apply_imputer(df_subset: pd.DataFrame, feature_cols: list[str], stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    df_temp = interpolate_within_location(df_subset, feature_cols)

    if stats is None:
        stats = build_imputer_stats(df_temp, feature_cols)

    key_series = pd.Series(list(zip(df_temp['Location_Name'], df_temp['Month'])), index=df_temp.index)

    for col in feature_cols:
        month_values = key_series.map(stats['month_lookup'][col])
        location_values = df_temp['Location_Name'].map(stats['location_lookup'][col])

        df_temp[col] = df_temp[col].fillna(month_values)
        df_temp[col] = df_temp[col].fillna(location_values)
        df_temp[col] = df_temp[col].fillna(stats['global_means'][col])

    return df_temp, stats


def prepare_features(df_subset: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    X = df_subset[feature_cols].copy()
    y = df_subset['red_tide_binary'].copy()
    return X, y


def evaluate_split(
    split_config: dict,
    df: pd.DataFrame,
    feature_cols: list[str],
    model_params: dict,
) -> dict:
    train_start = pd.Timestamp(split_config['train_start'])
    train_end = pd.Timestamp(split_config['train_end'])
    test_start = pd.Timestamp(split_config['test_start'])
    test_end = pd.Timestamp(split_config['test_end'])

    train_mask = (df['Date'] >= train_start) & (df['Date'] <= train_end)
    test_mask = (df['Date'] >= test_start) & (df['Date'] <= test_end)

    train_df = df.loc[train_mask].copy().reset_index(drop=True)
    test_df = df.loc[test_mask].copy().reset_index(drop=True)

    print(f"{split_config['name']}: {split_config['train_start']} to {train_end.date()} -> {test_start.date()} to {test_end.date()}")
    print(f"  Train rows: {len(train_df):,} | Test rows: {len(test_df):,}")

    train_imputed, imputer_stats = apply_imputer(train_df, feature_cols)
    test_imputed, _ = apply_imputer(test_df, feature_cols, imputer_stats)

    train_missing = train_imputed[feature_cols].isna().sum().sum()
    test_missing = test_imputed[feature_cols].isna().sum().sum()
    print(f"  Missing after imputation - train: {train_missing:,}, test: {test_missing:,}")

    X_train, y_train = prepare_features(train_imputed, feature_cols)
    X_test, y_test = prepare_features(test_imputed, feature_cols)

    model = XGBClassifier(**model_params)
    fit_start = perf_counter()
    model.fit(X_train, y_train)
    train_time_seconds = perf_counter() - fit_start

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    try:
        auc_roc = roc_auc_score(y_test, y_prob)
    except ValueError:
        auc_roc = float('nan')

    metrics = {
        'split': split_config['name'],
        'train_period': f"{split_config['train_start']} to {split_config['train_end']}",
        'test_period': f"{split_config['test_start']} to {test_end.date()}",
        'train_rows': len(train_df),
        'test_rows': len(test_df),
        'train_time_seconds': train_time_seconds,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'auc_roc': auc_roc,
        'positive_rate_train': y_train.mean(),
        'positive_rate_test': y_test.mean(),
    }

    print(
        f"  Metrics: Acc={metrics['accuracy']:.4f}, Prec={metrics['precision']:.4f}, "
        f"Rec={metrics['recall']:.4f}, F1={metrics['f1_score']:.4f}, AUC={metrics['auc_roc']:.4f}"
    )
    print(f"  Training runtime: {train_time_seconds:.2f} seconds")
    print()

    return metrics


def summarize_results(results_df: pd.DataFrame) -> pd.DataFrame:
    metric_columns = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc', 'train_time_seconds']
    summary_rows = []

    for metric in metric_columns:
        summary_rows.append({
            'metric': metric,
            'mean': results_df[metric].mean(),
            'std': results_df[metric].std(ddof=1),
            'min': results_df[metric].min(),
            'max': results_df[metric].max(),
        })

    return pd.DataFrame(summary_rows)


def write_summary_text(results_df: pd.DataFrame, summary_df: pd.DataFrame, output_path: Path, model_params: dict, dataset_end: pd.Timestamp) -> None:
    with open(output_path, 'w', encoding='utf-8') as handle:
        handle.write('XGBoost Six-Window Evaluation Summary\n')
        handle.write('=' * 60 + '\n\n')
        handle.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        handle.write(f"Dataset end date: {dataset_end.date()}\n\n")

        handle.write('Model parameters:\n')
        for key, value in model_params.items():
            handle.write(f"  {key}: {value}\n")

        handle.write('\nPer-split results:\n')
        for _, row in results_df.iterrows():
            handle.write(
                f"  {row['split']}: Acc={row['accuracy']:.4f}, Prec={row['precision']:.4f}, "
                f"Rec={row['recall']:.4f}, F1={row['f1_score']:.4f}, AUC={row['auc_roc']:.4f}, "
                f"TrainTime={row['train_time_seconds']:.2f}s\n"
            )

        handle.write('\nAggregate metrics:\n')
        for _, row in summary_df.iterrows():
            handle.write(
                f"  {row['metric']}: mean={row['mean']:.4f}, std={row['std']:.4f}, "
                f"min={row['min']:.4f}, max={row['max']:.4f}\n"
            )


def train_final_model(df: pd.DataFrame, feature_cols: list[str], model_params: dict) -> tuple[XGBClassifier, float]:
    print("Training final model on the full available dataset...")
    full_imputed, _ = apply_imputer(df, feature_cols)
    X_full, y_full = prepare_features(full_imputed, feature_cols)

    final_model = XGBClassifier(**model_params)
    fit_start = perf_counter()
    final_model.fit(X_full, y_full)
    fit_time_seconds = perf_counter() - fit_start

    return final_model, fit_time_seconds


def main() -> None:
    print_header()
    validate_splits_one_year(SPLITS)
    print("Step 2: Applying Hybrid Gap-Type Adaptive imputation within each split...")
    print("  Temporal interpolation limit: 14 days")
    print("  Long-gap fallback: Location x Month -> Location -> Global mean")
    print()

    df, feature_cols = prepare_data(DATA_PATH)

    print(f"Step 3: Preparing features for {len(feature_cols)} predictor columns...")
    print(f"[OK] Feature columns: {feature_cols}")
    print(f"[OK] Class imbalance ratio: {(df['red_tide_binary'] == 0).sum() / (df['red_tide_binary'] == 1).sum():.2f}:1 (non-bloom:bloom)")
    print()

    model_params = load_best_params(BEST_PARAMS_PATH)
    model_params.update({
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'random_state': 42,
        'n_jobs': -1,
    })

    print("Step 4: Evaluating XGBoost across 6 expanding time windows...")
    print(f"[OK] Loaded tuned hyperparameters from: {BEST_PARAMS_PATH}")
    print()

    dataset_end = df['Date'].max()
    split_results = []
    for split_config in SPLITS:
        split_result = evaluate_split(
            split_config=split_config,
            df=df,
            feature_cols=feature_cols,
            model_params=model_params,
        )
        split_results.append(split_result)

    results_df = pd.DataFrame(split_results)
    summary_df = summarize_results(results_df)

    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(results_df[['split', 'accuracy', 'precision', 'recall', 'f1_score', 'auc_roc', 'train_time_seconds']].to_string(index=False))
    print()
    print("Aggregate metrics:")
    for _, row in summary_df.iterrows():
        print(f"  {row['metric']}: mean={row['mean']:.4f}, std={row['std']:.4f}, min={row['min']:.4f}, max={row['max']:.4f}")
    print()

    RESULTS_DIR.mkdir(exist_ok=True)

    results_csv_path = RESULTS_DIR / 'temporal_window_results.csv'
    results_df.to_csv(results_csv_path, index=False)
    print(f"[OK] Split results saved to: {results_csv_path}")

    summary_csv_path = RESULTS_DIR / 'temporal_window_summary.csv'
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"[OK] Summary metrics saved to: {summary_csv_path}")

    summary_txt_path = RESULTS_DIR / 'temporal_window_summary.txt'
    write_summary_text(results_df, summary_df, summary_txt_path, model_params, dataset_end)
    print(f"[OK] Summary text saved to: {summary_txt_path}")

    final_model, final_fit_time = train_final_model(df, feature_cols, model_params)
    model_path = RESULTS_DIR / 'best_xgboost_model.json'
    final_model.save_model(str(model_path))
    print(f"[OK] Final model saved to: {model_path}")
    print(f"[OK] Final model training runtime: {final_fit_time:.2f} seconds")

    best_params_path = RESULTS_DIR / 'best_parameters.txt'
    with open(best_params_path, 'w', encoding='utf-8') as handle:
        handle.write('XGBoost Best Hyperparameters\n')
        handle.write('=' * 50 + '\n\n')
        handle.write('Best parameters used for the six-window evaluation:\n')
        for param, value in model_params.items():
            if param in {'objective', 'eval_metric', 'random_state', 'n_jobs'}:
                continue
            handle.write(f"  {param}: {value}\n")
        handle.write('\nSix-window aggregate metrics:\n')
        for _, row in summary_df.iterrows():
            handle.write(f"  {row['metric']}: mean={row['mean']:.4f}, std={row['std']:.4f}\n")
        handle.write(f"\nFinal model training runtime: {final_fit_time:.2f} seconds\n")
    print(f"[OK] Best parameters summary saved to: {best_params_path}")

    print()
    print("=" * 80)
    print("Training completed successfully!")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == '__main__':
    main()
>>>>>>> Stashed changes
