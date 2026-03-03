"""
==============================================================================
XGBoost Training Pipeline
==============================================================================
Purpose:
    For each of the 11 imputation methods sourced from Tasks 2 & 3, apply
    the method to each rolling-origin split, engineer features, train an
    XGBoost regression model, and evaluate downstream CHL prediction quality.

    This file:
        • Imports imputation functions directly from Tasks 2 & 3 (no
          reimplementation of logic).
        • Wraps them into a unified apply_imputation() dispatcher.
        • Runs the full train → predict → evaluate loop per method × split.
        • Saves per-split results and SHAP importance CSVs.

Validation framework:
    Task 1 rolling_origin splits 1-4 (90-day test windows, temporal order).

Output written to:
    task4_results/xgboost_results_per_split.csv
    task4_results/feature_importance/feature_importance_<method>.csv

==============================================================================
"""

import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)

# SHAP is loaded lazily inside compute_shap_importance().
# If shap/numba are not properly installed the pipeline continues without SHAP.

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path setup — inject Task 2 & 3 code directories so we can import directly
# ---------------------------------------------------------------------------

_THIS_DIR   = Path(__file__).resolve().parent          # task_4/code/
_TASK4_DIR  = _THIS_DIR.parent                         # task_4/
_ROOT       = _TASK4_DIR.parent                        # repo root

_TASK1_DIR  = _ROOT / "task_1"
_TASK2_CODE = _ROOT / "task_2" / "code"
_TASK3_CODE = _ROOT / "task_3" / "code"

for _p in [str(_TASK2_CODE), str(_TASK3_CODE)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Task 2 imports
from task2_temporal_imputation import (          # noqa: E402
    impute_dataset as t2_impute_dataset,
)

# Task 3 imports
from task3_spatial_imputation import (           # noqa: E402
    advection_impute,
    cross_location_knn_impute,
    cross_location_regression_impute,
    distance_weighted_impute,
    eof_pca_impute,
    hybrid_adaptive_impute,
    hybrid_ensemble_impute,
    hybrid_sequential_impute,
    kriging_impute,
)

# Local import
from task4_feature_engineering import (          # noqa: E402
    build_feature_matrix,
    get_train_test_split,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VARIABLES_TO_IMPUTE: List[str] = [
    "CHL", "mlotst", "no3", "o2", "po4", "so", "thetao", "uo", "vo",
    "NDVI_daily", "NDVI_raw", "precip_mm_day", "wind_speed_ms",
    "wind_u_ms", "wind_v_ms",
]

LOCATIONS: List[str] = ["Gigantes Polygon", "Roxas Polygon"]

# 11 imputation methods: key → display name
IMPUTATION_METHODS: Dict[str, str] = {
    "linear_interpolation":        "Linear Interpolation",
    "climatological":              "Climatological Substitution",
    "cross_location_regression":   "Cross-Location Regression",
    "cross_location_knn":          "Cross-Location KNN",
    "distance_weighted":           "Distance-Weighted Average",
    "advection":                   "Advection-Based",
    "eof_pca":                     "EOF/PCA Spatial Modes",
    "kriging":                     "Spatial Kriging",
    "hybrid_sequential":           "Hybrid: Sequential Temporal→Spatial",
    "hybrid_ensemble":             "Hybrid: Temporal-Spatial Ensemble",
    "hybrid_adaptive":             "Hybrid: Gap-Type Adaptive",
}

NUM_SPLITS: int = 4
SPLIT_TYPE: str = "rolling_origin"       # Task 1 folder

# CHL threshold for post-hoc bloom classification (µg/L)
BLOOM_THRESHOLD: float = 1.0

# Top N features to persist per method
TOP_N_FEATURES: int = 15

# XGBoost hyperparameters
XGB_PARAMS: Dict = {
    "objective":          "reg:squarederror",
    "n_estimators":       500,
    "max_depth":          6,
    "learning_rate":      0.05,
    "subsample":          0.8,
    "colsample_bytree":   0.8,
    "early_stopping_rounds": 50,
    "random_state":       42,
    "n_jobs":             -1,
    "verbosity":          0,
}

# Output paths (relative to task_4/)
OUTPUT_DIR        = _TASK4_DIR / "task4_results"
PER_SPLIT_CSV     = OUTPUT_DIR / "xgboost_results_per_split.csv"
FEAT_IMP_DIR      = OUTPUT_DIR / "feature_importance"


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_baseline() -> pd.DataFrame:
    """Load the ground-truth baseline dataset from Task 1."""
    path = _TASK1_DIR / "task1_data" / "Task1_Combined_Baseline_Daily.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def load_split_data(split_num: int) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Load masked data, mask DataFrame, and config for one rolling-origin split.

    Args:
        split_num: Integer 1-4.

    Returns:
        masked_data : long-format DataFrame with NaN in test window
        mask_df     : long-format DataFrame with boolean mask values
        config      : dict parsed from config.json
    """
    split_dir = (
        _TASK1_DIR / "masked_datasets" / SPLIT_TYPE / f"split_{split_num}"
    )
    masked_data = pd.read_csv(split_dir / "masked_data.csv")
    masked_data["Date"] = pd.to_datetime(masked_data["Date"])

    mask_df = pd.read_csv(split_dir / "mask.csv")
    mask_df["Date"] = masked_data["Date"]
    mask_df["Location_Name"] = masked_data["Location_Name"]

    with open(split_dir / "config.json") as f:
        config = json.load(f)

    return masked_data, mask_df, config


# ---------------------------------------------------------------------------
# Imputation dispatcher
# ---------------------------------------------------------------------------

def apply_imputation(
    masked_data: pd.DataFrame,
    baseline_data: pd.DataFrame,
    method_key: str,
    mask_type: str = "rolling_origin",
) -> pd.DataFrame:
    """
    Apply one imputation method and return a fully-filled DataFrame.

    For Task 2 methods, delegates to task2_temporal_imputation.impute_dataset().
    For Task 3 methods, calls per-variable, per-location functions imported
    from task3_spatial_imputation, then reassembles the full DataFrame.

    Args:
        masked_data   : Long-format DataFrame with NaN gaps.
        baseline_data : Ground-truth long-format DataFrame (no NaN).
        method_key    : Key from IMPUTATION_METHODS dict.
        mask_type     : Gap pattern name (used by hybrid_adaptive).

    Returns:
        Long-format DataFrame with all NaN values filled.
    """
    # ── Task 2 temporal methods ───────────────────────────────────────────
    if method_key in ("linear_interpolation", "climatological"):
        t2_key = (
            "linear_interpolation" if method_key == "linear_interpolation"
            else "climatological"
        )
        return t2_impute_dataset(masked_data, baseline_data, t2_key)

    # ── Task 3 spatial / hybrid methods ───────────────────────────────────
    # Sort by Location_Name then Date and reset the integer index so each
    # location's rows form a contiguous block [0, 1, …, N_loc-1].
    # Task 3 functions filter the DataFrame internally with a boolean mask
    # and then call pd.merge(), which always returns a fresh [0, 1, …] index.
    # When the input has alternating Gigantes/Roxas rows the filtered subset
    # has non-contiguous indices [0, 2, 4, …] which pandas cannot align with
    # the merged result, causing "IndexingError: Unalignable boolean Series".
    # Resetting the index here fixes this without touching Task 3 code.
    masked_clean = (
        masked_data.sort_values(["Location_Name", "Date"])
        .reset_index(drop=True)
    )
    baseline_clean = (
        baseline_data.sort_values(["Location_Name", "Date"])
        .reset_index(drop=True)
    )
    result = masked_clean.copy()

    for location in LOCATIONS:
        loc_mask = result["Location_Name"] == location

        for var in VARIABLES_TO_IMPUTE:
            try:
                if method_key == "cross_location_regression":
                    imputed = cross_location_regression_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "cross_location_knn":
                    imputed = cross_location_knn_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "distance_weighted":
                    imputed = distance_weighted_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "advection":
                    imputed = advection_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "eof_pca":
                    imputed = eof_pca_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "kriging":
                    imputed = kriging_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "hybrid_sequential":
                    imputed = hybrid_sequential_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "hybrid_ensemble":
                    imputed = hybrid_ensemble_impute(
                        masked_clean, var, baseline_clean, location
                    )
                elif method_key == "hybrid_adaptive":
                    imputed = hybrid_adaptive_impute(
                        masked_clean, var, baseline_clean, location, mask_type
                    )
                else:
                    # Unrecognised method — leave as-is (forward-fill fallback)
                    imputed = (
                        masked_clean[masked_clean["Location_Name"] == location][var]
                        .ffill()
                        .bfill()
                    )

                # Write imputed Series back into result
                # Align by resetting index to match loc-filtered result rows
                loc_indices = result.index[loc_mask]
                imputed_vals = imputed.reset_index(drop=True)

                if len(imputed_vals) == loc_mask.sum():
                    result.loc[loc_mask, var] = imputed_vals.values
                else:
                    # Length mismatch guard — keep original
                    pass

            except Exception as exc:
                print(
                    f"    [WARN] {method_key} / {var} / {location[:8]}: "
                    f"{exc.__class__.__name__}: {str(exc)[:60]}"
                )

    # Last-resort fill for any remaining NaN (edge of series, etc.)
    result[VARIABLES_TO_IMPUTE] = (
        result.groupby("Location_Name")[VARIABLES_TO_IMPUTE]
        .transform(lambda s: s.ffill().bfill())
    )
    # Absolute fallback: column median
    for var in VARIABLES_TO_IMPUTE:
        if result[var].isna().any():
            result[var] = result[var].fillna(result[var].median())

    return result


# ---------------------------------------------------------------------------
# XGBoost training
# ---------------------------------------------------------------------------

def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> xgb.XGBRegressor:
    """
    Train XGBoost with early stopping on a validation set.

    Args:
        X_train, y_train : Training features and target.
        X_val, y_val     : Validation features and target (early-stopping set).

    Returns:
        Fitted XGBRegressor.
    """
    model = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return model


# ---------------------------------------------------------------------------
# SHAP importance
# ---------------------------------------------------------------------------

def compute_feature_importance(
    model: xgb.XGBRegressor,
    X_test: pd.DataFrame,
    top_n: int = TOP_N_FEATURES,
) -> pd.DataFrame:
    """
    Compute feature importance scores on X_test and return the top-N features.

    Attempts SHAP TreeExplainer first (mean absolute Shapley values — exact for
    tree models).  Falls back to XGBoost native gain-based importance when shap
    is not installed or fails.  The column is labelled 'mean_abs_importance' in
    both cases; callers should NOT assume this is SHAP unless shap is confirmed
    installed.

    Args:
        model  : Trained XGBRegressor.
        X_test : Test feature matrix.
        top_n  : Number of top features to return.

    Returns:
        DataFrame with columns ['feature', 'mean_abs_importance'] sorted descending.
    """
    try:
        import shap as _shap  # lazy import — only runs when this function is called
        explainer   = _shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)          # (n_test, n_features)
        mean_abs    = np.abs(shap_values).mean(axis=0)
    except Exception:  # noqa: BLE001  — shap missing, broken, or any other error
        # Fallback: XGBoost built-in gain-based importance
        gains    = model.get_booster().get_score(importance_type="gain")
        mean_abs = np.array(
            [gains.get(f, 0.0) for f in X_test.columns], dtype=float
        )

    importance_df = (
        pd.DataFrame({"feature": X_test.columns, "mean_abs_importance": mean_abs})
        .sort_values("mean_abs_importance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return importance_df


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    bloom_threshold: float = BLOOM_THRESHOLD,
) -> Dict[str, float]:
    """
    Compute regression and thresholded classification metrics.

    Regression  : RMSE, MAE, R²
    Classification (post-hoc bloom threshold):
        F1-score for the bloom class (label=1)
        AUC-ROC

    Args:
        y_true          : Ground-truth CHL values.
        y_pred          : XGBoost CHL predictions.
        bloom_threshold : CHL value above which a bloom event is flagged.

    Returns:
        Dict with keys: rmse, mae, r2, f1, auc
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    valid = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true, y_pred = y_true[valid], y_pred[valid]

    if len(y_true) == 0:
        return dict(rmse=np.nan, mae=np.nan, r2=np.nan, f1=np.nan, auc=np.nan)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))

    # Thresholded bloom classification
    true_labels = (y_true >= bloom_threshold).astype(int)
    pred_labels = (y_pred >= bloom_threshold).astype(int)

    if true_labels.sum() == 0 or true_labels.sum() == len(true_labels):
        # Can't compute AUC if only one class present
        f1  = float(f1_score(true_labels, pred_labels, zero_division=0))
        auc = np.nan
    else:
        f1  = float(f1_score(true_labels, pred_labels, zero_division=0))
        auc = float(roc_auc_score(true_labels, y_pred))

    return dict(rmse=rmse, mae=mae, r2=r2, f1=f1, auc=auc)


# ---------------------------------------------------------------------------
# Single method × split runner
# ---------------------------------------------------------------------------

def run_one_split(
    method_key: str,
    split_num: int,
    baseline_data: pd.DataFrame,
) -> Optional[Dict]:
    """
    Full pipeline for one imputation method × one rolling-origin split.

    Steps:
        1. Load masked data for the split.
        2. Apply imputation.
        3. Build feature matrix.
        4. Temporal train/test split (cutoff dates from config.json).
        5. Create 80/20 internal train/val split within training data for
           XGBoost early stopping (on training window only, no leakage).
        6. Train XGBoost.
        7. Evaluate on test window.
        8. Compute SHAP values.

    Args:
        method_key    : Key from IMPUTATION_METHODS.
        split_num     : Integer 1-4.
        baseline_data : Ground-truth DataFrame.

    Returns:
        Dict of metrics or None on unrecoverable error.
    """
    print(f"    Split {split_num}/{NUM_SPLITS}...", end=" ", flush=True)

    try:
        # 1. Load split
        masked_data, mask_df, config = load_split_data(split_num)
        cfg = config["config"]
        cutoff_date = cfg["cutoff_date"]
        test_start  = cfg["test_start"]
        test_end    = cfg["test_end"]

        # 2. Impute
        imputed_data = apply_imputation(
            masked_data, baseline_data, method_key, mask_type=SPLIT_TYPE
        )

        # 3. Feature matrix
        feat_matrix = build_feature_matrix(imputed_data, mask_df)

        # 4. Temporal split
        X_train_full, y_train_full, X_test, y_test = get_train_test_split(
            feat_matrix, cutoff_date, test_start, test_end
        )

        if len(X_train_full) < 30 or len(X_test) == 0:
            print("SKIP (insufficient data)")
            return None

        # 5. Internal train/val split on the TRAINING window only (80/20)
        val_cutoff = int(len(X_train_full) * 0.8)
        X_tr, y_tr = X_train_full.iloc[:val_cutoff], y_train_full.iloc[:val_cutoff]
        X_val, y_val = X_train_full.iloc[val_cutoff:], y_train_full.iloc[val_cutoff:]

        # 6. Train XGBoost
        model = train_xgboost(X_tr, y_tr, X_val, y_val)

        # 7. Predict on ground-truth test window
        #    Use baseline CHL as y_test to evaluate against true values
        baseline_test = baseline_data.copy()
        baseline_test["Date"] = pd.to_datetime(baseline_test["Date"])
        t_start_ts = pd.Timestamp(test_start)
        t_end_ts   = pd.Timestamp(test_end)
        true_chl_gig = (
            baseline_test[
                (baseline_test["Location_Name"] == "Gigantes Polygon")
                & (baseline_test["Date"] >= t_start_ts)
                & (baseline_test["Date"] <= t_end_ts)
            ]
            .set_index("Date")["CHL"]
        )

        # Align predictions with true values
        y_pred_series = pd.Series(
            model.predict(X_test), index=X_test.index, name="pred_CHL"
        )
        aligned = pd.concat([true_chl_gig.rename("true_CHL"), y_pred_series], axis=1).dropna()

        metrics = compute_metrics(
            aligned["true_CHL"].values,
            aligned["pred_CHL"].values,
        )
        print(
            f"RMSE={metrics['rmse']:.4f}  R²={metrics['r2']:.4f}  "
            f"F1={metrics['f1']:.4f}  AUC={metrics['auc']:.4f}"
        )

        # 8. Feature importance on test set
        feat_imp_df = compute_feature_importance(model, X_test)
        feat_imp_df["method"]    = method_key
        feat_imp_df["split_num"] = split_num

        return {
            "method_key":    method_key,
            "method_name":   IMPUTATION_METHODS[method_key],
            "split_num":     split_num,
            "cutoff_date":   cutoff_date,
            "test_start":    test_start,
            "test_end":      test_end,
            "n_train":       len(X_tr),
            "n_test":        len(aligned),
            **metrics,
            "_feat_imp_df":  feat_imp_df,   # internal; stripped before saving
        }

    except Exception as exc:
        import traceback
        print(f"ERROR — {exc.__class__.__name__}: {str(exc)[:80]}")
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# Outer loop: all methods × all splits
# ---------------------------------------------------------------------------

def run_all(
    methods: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Iterate over every imputation method and every rolling-origin split,
    train XGBoost, evaluate, and persist results.

    Args:
        methods: Subset of IMPUTATION_METHODS to run (default: all 11).

    Returns:
        per_split_df : DataFrame with one row per method × split.
    """
    if methods is None:
        methods = IMPUTATION_METHODS

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FEAT_IMP_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLoading baseline data...")
    baseline_data = load_baseline()
    print(f"  {len(baseline_data)} rows  |  "
          f"{baseline_data['Date'].min().date()} → {baseline_data['Date'].max().date()}")

    all_results: List[Dict] = []
    all_feat_imp: Dict[str, List[pd.DataFrame]] = {k: [] for k in methods}

    total = len(methods) * NUM_SPLITS
    done  = 0

    for method_key, method_name in methods.items():
        print(f"\n{'─'*65}")
        print(f"  Method [{done // NUM_SPLITS + 1}/{len(methods)}]: {method_name}")
        print(f"{'─'*65}")

        for split_num in range(1, NUM_SPLITS + 1):
            result = run_one_split(method_key, split_num, baseline_data)
            done += 1

            if result is not None:
                feat_imp_df = result.pop("_feat_imp_df")
                all_feat_imp[method_key].append(feat_imp_df)
                all_results.append(result)

        # Save aggregated feature importance for this method
        if all_feat_imp[method_key]:
            combined_imp = (
                pd.concat(all_feat_imp[method_key])
                .groupby("feature")["mean_abs_importance"]
                .mean()
                .sort_values(ascending=False)
                .head(TOP_N_FEATURES)
                .reset_index()
            )
            combined_imp["method"] = method_key
            imp_path = FEAT_IMP_DIR / f"feature_importance_{method_key}.csv"
            combined_imp.to_csv(imp_path, index=False)
            print(f"  → Feature importance saved: {imp_path.name}")

    # Persist per-split results
    per_split_df = pd.DataFrame(all_results)
    if not per_split_df.empty:
        per_split_df.to_csv(PER_SPLIT_CSV, index=False)
        print(f"\n✓ Per-split results saved → {PER_SPLIT_CSV}")
    else:
        print("\n[WARN] No results collected.")

    return per_split_df
