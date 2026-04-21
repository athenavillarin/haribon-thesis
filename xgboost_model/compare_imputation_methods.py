"""
Imputation Method Comparison for XGBoost
=========================================
This script compares different imputation methods using the same six
expanding temporal windows as the main XGBoost training workflow.

Methods compared:
1. Hybrid Gap-Type Adaptive (14-day limit + climatological fallback)
2. Pure Climatological Substitution
3. Linear Interpolation only
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
        'test_end': None,
    },
]


def print_header() -> None:
    print("=" * 80)
    print("Imputation Method Comparison for XGBoost")
    print("=" * 80)
    print()


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


def prepare_base_data(data_path: Path) -> tuple[pd.DataFrame, list[str]]:
    print("Loading base dataset...")
    df_base = pd.read_csv(data_path)
    df_base['Date'] = pd.to_datetime(df_base['Date'])
    df_base['Month'] = df_base['Date'].dt.month
    df_base = df_base.sort_values(['Location_Name', 'Date']).reset_index(drop=True)
    df_base = df_base.dropna(subset=['red_tide_label']).reset_index(drop=True)
    df_base['red_tide_binary'] = (df_base['red_tide_label'] >= 0.5).astype(int)

    feature_cols = [
        col for col in df_base.columns
        if col not in ['red_tide', 'red_tide_label', 'red_tide_binary', 'Date', 'Location_Name', 'Month']
    ]

    print(f"[OK] Dataset: {df_base.shape[0]} rows x {df_base.shape[1]} columns")
    print(f"[OK] Features: {len(feature_cols)}")
    print(f"[OK] Red tide binary distribution: {df_base['red_tide_binary'].value_counts().to_dict()}")
    print()

    return df_base, feature_cols


def interpolate_within_location(df_subset: pd.DataFrame, feature_cols: list[str], limit: int | None) -> pd.DataFrame:
    df_temp = df_subset.sort_values(['Location_Name', 'Date']).reset_index(drop=True).copy()
    for location in df_temp['Location_Name'].unique():
        location_mask = df_temp['Location_Name'] == location
        df_temp.loc[location_mask, feature_cols] = df_temp.loc[location_mask, feature_cols].interpolate(
            method='linear',
            limit=limit,
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


def fill_with_stats(df_temp: pd.DataFrame, feature_cols: list[str], stats: dict) -> pd.DataFrame:
    key_series = pd.Series(list(zip(df_temp['Location_Name'], df_temp['Month'])), index=df_temp.index)

    for col in feature_cols:
        month_values = key_series.map(stats['month_lookup'][col])
        location_values = df_temp['Location_Name'].map(stats['location_lookup'][col])

        df_temp[col] = df_temp[col].fillna(month_values)
        df_temp[col] = df_temp[col].fillna(location_values)
        df_temp[col] = df_temp[col].fillna(stats['global_means'][col])

    return df_temp


def impute_hybrid_adaptive(df_subset: pd.DataFrame, feature_cols: list[str], stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    df_temp = interpolate_within_location(df_subset, feature_cols, limit=14)
    if stats is None:
        stats = build_imputer_stats(df_temp, feature_cols)
    df_temp = fill_with_stats(df_temp, feature_cols, stats)
    return df_temp, stats


def impute_climatological_only(df_subset: pd.DataFrame, feature_cols: list[str], stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    df_temp = df_subset.sort_values(['Location_Name', 'Date']).reset_index(drop=True).copy()
    if stats is None:
        stats = build_imputer_stats(df_temp, feature_cols)
    df_temp = fill_with_stats(df_temp, feature_cols, stats)
    return df_temp, stats


def impute_linear_only(df_subset: pd.DataFrame, feature_cols: list[str], stats: dict | None = None) -> tuple[pd.DataFrame, dict]:
    df_temp = interpolate_within_location(df_subset, feature_cols, limit=None)
    if stats is None:
        stats = build_imputer_stats(df_temp, feature_cols)
    df_temp = fill_with_stats(df_temp, feature_cols, stats)
    return df_temp, stats


def prepare_features(df_subset: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    X = df_subset[feature_cols].copy()
    y = df_subset['red_tide_binary'].copy()
    return X, y


def evaluate_method_on_split(
    method_name: str,
    impute_func,
    split_config: dict,
    df: pd.DataFrame,
    feature_cols: list[str],
    model_params: dict,
    test_end_override: str | None = None,
) -> dict:
    train_start = pd.Timestamp(split_config['train_start'])
    train_end = pd.Timestamp(split_config['train_end'])
    test_start = pd.Timestamp(split_config['test_start'])
    test_end_raw = test_end_override or split_config['test_end']
    test_end = pd.Timestamp(test_end_raw) if test_end_raw is not None else None

    train_mask = (df['Date'] >= train_start) & (df['Date'] <= train_end)
    if test_end is None:
        test_mask = df['Date'] >= test_start
    else:
        test_mask = (df['Date'] >= test_start) & (df['Date'] <= test_end)

    train_df = df.loc[train_mask].copy().reset_index(drop=True)
    test_df = df.loc[test_mask].copy().reset_index(drop=True)

    train_imputed, imputer_stats = impute_func(train_df, feature_cols)
    test_imputed, _ = impute_func(test_df, feature_cols, imputer_stats)

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

    return {
        'Method': method_name,
        'Split': split_config['name'],
        'Train_Period': f"{split_config['train_start']} to {split_config['train_end']}",
        'Test_Period': f"{split_config['test_start']} to {test_end.date() if test_end is not None else 'end of data'}",
        'Train_Rows': len(train_df),
        'Test_Rows': len(test_df),
        'Train_Time_Seconds': train_time_seconds,
        'Accuracy': accuracy_score(y_test, y_pred),
        'Precision': precision_score(y_test, y_pred, zero_division=0),
        'Recall': recall_score(y_test, y_pred, zero_division=0),
        'F1_Score': f1_score(y_test, y_pred, zero_division=0),
        'AUC_ROC': auc_roc,
    }


def summarize_results(results_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    metric_columns = ['Accuracy', 'Precision', 'Recall', 'F1_Score', 'AUC_ROC', 'Train_Time_Seconds']

    for method_name, method_group in results_df.groupby('Method'):
        summary_rows.append({
            'Method': method_name,
            'Mean_Accuracy': method_group['Accuracy'].mean(),
            'Std_Accuracy': method_group['Accuracy'].std(ddof=1),
            'Mean_Precision': method_group['Precision'].mean(),
            'Std_Precision': method_group['Precision'].std(ddof=1),
            'Mean_Recall': method_group['Recall'].mean(),
            'Std_Recall': method_group['Recall'].std(ddof=1),
            'Mean_F1_Score': method_group['F1_Score'].mean(),
            'Std_F1_Score': method_group['F1_Score'].std(ddof=1),
            'Mean_AUC_ROC': method_group['AUC_ROC'].mean(),
            'Std_AUC_ROC': method_group['AUC_ROC'].std(ddof=1),
            'Mean_Train_Time_Seconds': method_group['Train_Time_Seconds'].mean(),
            'Std_Train_Time_Seconds': method_group['Train_Time_Seconds'].std(ddof=1),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values('Mean_AUC_ROC', ascending=False).reset_index(drop=True)
    return summary_df


def main() -> None:
    print_header()

    df_base, feature_cols = prepare_base_data(DATA_PATH)

    print("Loading best hyperparameters from previous training...")
    best_params = load_best_params(BEST_PARAMS_PATH)
    best_params.update({
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'random_state': 42,
        'n_jobs': -1,
    })
    print("[OK] Using tuned XGBoost hyperparameters")
    print()

    methods = {
        'Hybrid: Gap-Type Adaptive (14-day)': impute_hybrid_adaptive,
        'Climatological Substitution': impute_climatological_only,
        'Linear Interpolation (no limit)': impute_linear_only,
    }

    print("Comparing imputation methods across 6 expanding time windows...")
    print()

    results = []
    for method_name, impute_func in methods.items():
        print(f"Testing: {method_name}")
        print("-" * 80)
        for split_config in SPLITS:
            split_result = evaluate_method_on_split(
                method_name=method_name,
                impute_func=impute_func,
                split_config=split_config,
                df=df_base,
                feature_cols=feature_cols,
                model_params=best_params,
                test_end_override=None if split_config['test_end'] is not None else str(df_base['Date'].max().date()),
            )
            results.append(split_result)
            print(
                f"  {split_result['Split']}: AUC={split_result['AUC_ROC']:.4f}, "
                f"F1={split_result['F1_Score']:.4f}, TrainTime={split_result['Train_Time_Seconds']:.2f}s"
            )
        print()

    results_df = pd.DataFrame(results)
    summary_df = summarize_results(results_df)

    print("=" * 80)
    print("FINAL COMPARISON RESULTS")
    print("=" * 80)
    print()
    print(summary_df[['Method', 'Mean_AUC_ROC', 'Std_AUC_ROC', 'Mean_F1_Score', 'Mean_Train_Time_Seconds']].to_string(index=False))
    print()

    best_method = summary_df.iloc[0]
    print("Ranking by Mean AUC:")
    for rank, (_, row) in enumerate(summary_df.iterrows(), 1):
        print(f"  Rank {rank}: {row['Method']} | AUC={row['Mean_AUC_ROC']:.4f} (+/-{row['Std_AUC_ROC']:.4f})")
    print()

    output_path = RESULTS_DIR / "imputation_comparison_temporal_results.csv"
    summary_path = RESULTS_DIR / "imputation_comparison_temporal_summary.csv"
    RESULTS_DIR.mkdir(exist_ok=True)
    results_df.to_csv(output_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    print(f"[OK] Split-level results saved to: {output_path}")
    print(f"[OK] Summary results saved to: {summary_path}")
    print()

    print("RECOMMENDATION")
    print("=" * 80)
    print(f"Best imputation method by mean AUC: {best_method['Method']}")
    print(f"Expected Mean AUC: {best_method['Mean_AUC_ROC']:.4f} +/- {best_method['Std_AUC_ROC']:.4f}")
    print(f"Mean training runtime: {best_method['Mean_Train_Time_Seconds']:.2f} seconds")
    print()
    print("Six-window temporal evaluation is now used for all comparison results.")
    print("This makes the comparison consistent with the main XGBoost training workflow.")
    print()
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
