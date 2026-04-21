"""
XGBoost Model Training with HARIBON Methodology
================================================
This script implements:
1. Data preparation from Combined_Labeled.csv
2. Hybrid Gap-Type Adaptive imputation fitted per temporal split
3. Expanding-window evaluation with 6 fixed test windows
4. Metrics: Accuracy, Precision, Recall, F1-Score, AUC-ROC
5. Training runtime tracking and final model export
"""

from datetime import datetime
from pathlib import Path
from time import perf_counter
import re

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier


RESULTS_DIR = Path(__file__).parent / "results"
DATA_PATH = Path(__file__).parent.parent / "final_compiled_dataset" / "Combined_Labeled.csv"
BEST_PARAMS_PATH = RESULTS_DIR / "best_parameters.txt"

DEFAULT_BEST_PARAMS = {
    'subsample': 0.9,
    'scale_pos_weight': 5,
    'n_estimators': 500,
    'min_child_weight': 7,
    'max_depth': 8,
    'learning_rate': 0.2,
    'gamma': 0.2,
    'colsample_bytree': 0.9,
}

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
    final_model.save_model(model_path)
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
