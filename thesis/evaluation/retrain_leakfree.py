"""
retrain_leakfree.py
===================
Retrains the four existing model types without look-ahead and scores them
next to the baselines and the environment-driven model, all on the same rows.

Differences from the original training runs:
  - imputation uses past values and training-period climatology only
    (the original filled gaps from both directions and from all years)
  - early stopping uses the last 365 days of training across all sites
    (the original used the tail of the concatenated array, i.e. one site)
  - XGBoost hyperparameters are chosen on year-blocked folds
    (the original used non-temporal 3-fold CV)

Architectures, lookback, loss and feature list are unchanged. Models are saved
under saved_model/leakfree/ so the production artifacts are not touched.

Usage:
    cd evaluation
    python retrain_leakfree.py
    python retrain_leakfree.py --models xgboost env_model   # subset

Output:
    results/leakfree_per_split.csv
    results/leakfree_summary.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import MinMaxScaler

_THIS_DIR = Path(__file__).resolve().parent
_THESIS_DIR = _THIS_DIR.parent
for p in (_THESIS_DIR / "env_model", _THESIS_DIR / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from baselines import baseline_scores, build_test_frame, score_split, summarize  # noqa: E402
from ensemble_data import DEFAULT_DATASET_PATH, FEATURES, LOOKBACK, SPLITS, load_and_prepare  # noqa: E402
from features import build_features, impute_causal, load_daily, load_grid  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"
MODEL_DIR = _THIS_DIR / "saved_model" / "leakfree"

ALL_MODELS = ["lstm", "gru", "transformer", "xgboost", "env_model"]
HOLDOUT_DAYS = 365
SEED = 42

XGB_GRID = [
    dict(max_depth=d, learning_rate=lr, n_estimators=n, min_child_weight=mcw,
         subsample=0.8, colsample_bytree=0.8)
    for d in (3, 5) for lr in (0.03, 0.1) for n in (100, 300) for mcw in (5, 20)
]


def build_sequences(grid: pd.DataFrame, cfg: dict) -> SimpleNamespace:
    """Past-only imputation, then 30-day windows that predict the next day's label."""
    train_end = pd.Timestamp(cfg["train_end"])
    df = impute_causal(grid.copy(), grid["Date"] <= train_end, FEATURES)

    X_tr, y_tr, d_tr, X_te, y_te, d_te, l_te = [], [], [], [], [], [], []
    for loc, g in df.groupby("Location_Name", sort=False):
        X = g[FEATURES].to_numpy(dtype=np.float32)
        y = g["red_tide_binary"].to_numpy()
        dates = g["Date"].to_numpy()
        for t in range(LOOKBACK - 1, len(g) - 1):
            target = t + 1
            if np.isnan(y[target]):
                continue
            window = X[t - LOOKBACK + 1: t + 1]
            if dates[target] <= np.datetime64(train_end):
                X_tr.append(window); y_tr.append(y[target]); d_tr.append(dates[target])
            elif pd.Timestamp(cfg["test_start"]) <= dates[target] <= np.datetime64(pd.Timestamp(cfg["test_end"])):
                X_te.append(window); y_te.append(y[target]); d_te.append(dates[target]); l_te.append(loc)

    order = np.argsort(np.array(d_tr), kind="stable")
    X_tr = np.stack(X_tr)[order]
    scaler = MinMaxScaler(feature_range=(-1, 1)).fit(X_tr.reshape(-1, len(FEATURES)))

    def scale(a: np.ndarray) -> np.ndarray:
        return scaler.transform(a.reshape(-1, len(FEATURES))).reshape(a.shape).astype(np.float32)

    return SimpleNamespace(
        split_num=cfg["split_num"],
        train_end=cfg["train_end"],
        X_raw_train=X_tr,
        X_raw_test=np.stack(X_te),
        X_train=scale(X_tr),
        X_test=scale(np.stack(X_te)),
        y_train=np.array(y_tr, dtype=np.int64)[order],
        dates_train=np.array(d_tr)[order],
        y_test=np.array(y_te, dtype=np.int64),
        dates_test=np.array(d_te),
        locs_test=np.array(l_te, dtype=object),
    )


def _holdout_mask(s: SimpleNamespace) -> np.ndarray:
    cutoff = np.datetime64(pd.Timestamp(s.train_end) - pd.Timedelta(days=HOLDOUT_DAYS))
    return s.dates_train > cutoff


def train_rnn(s: SimpleNamespace, kind: str) -> np.ndarray:
    import tensorflow as tf
    from ensemble_inference import _build_gru_model, _build_lstm_model

    tf.keras.backend.clear_session()
    tf.random.set_seed(SEED)
    build = _build_lstm_model if kind == "lstm" else _build_gru_model
    model = build(n_features=len(FEATURES), lookback=LOOKBACK)

    def focal(y_true, y_pred, alpha=0.25, gamma=2.0):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        bce = -(y_true * tf.math.log(y_pred) + (1 - y_true) * tf.math.log(1 - y_pred))
        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
        return tf.reduce_mean(alpha_t * tf.pow(1 - p_t, gamma) * bce)

    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss=focal)
    hold = _holdout_mask(s)
    n_pos, n_neg = s.y_train[~hold].sum(), (~hold).sum() - s.y_train[~hold].sum()
    class_weight = {0: (n_pos + n_neg) / (2.0 * n_neg), 1: (n_pos + n_neg) / (2.0 * max(n_pos, 1))}
    model.fit(
        s.X_train[~hold], s.y_train[~hold].astype(np.float32),
        validation_data=(s.X_train[hold], s.y_train[hold].astype(np.float32)),
        epochs=60, batch_size=64, class_weight=class_weight, verbose=0,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6),
        ],
    )
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_DIR / f"{kind}_split{s.split_num}.keras")
    return model.predict(s.X_test, verbose=0).ravel()


def train_transformer(s: SimpleNamespace) -> np.ndarray:
    from ensemble_inference import predict_transformer
    # Training rows are sorted by date, so the trainer's last-20% validation
    # slice is the most recent period across all sites.
    split = SimpleNamespace(
        split_num=s.split_num, X_seq_train=s.X_raw_train, y_train=s.y_train,
        X_seq_test=s.X_raw_test,
    )
    return predict_transformer(split, saved_dir=MODEL_DIR, scenario="leakfree", fallback_retrain=True)


def train_xgboost(s: SimpleNamespace) -> np.ndarray:
    from xgboost import XGBClassifier
    X_tab, X_tab_test = s.X_train[:, -1, :], s.X_test[:, -1, :]
    years = pd.DatetimeIndex(s.dates_train).year.to_numpy()
    last_year = years.max()

    def make(params):
        pos = s.y_train.sum()
        return XGBClassifier(**params, scale_pos_weight=(len(s.y_train) - pos) / max(pos, 1),
                             objective="binary:logistic", eval_metric="auc",
                             random_state=SEED, n_jobs=-1)

    best, best_auc = XGB_GRID[0], -1.0
    for params in XGB_GRID:
        aucs = []
        for val_year in (last_year - 1, last_year):
            fit, val = years < val_year, years == val_year
            if len(np.unique(s.y_train[val])) < 2 or len(np.unique(s.y_train[fit])) < 2:
                continue
            p = make(params).fit(X_tab[fit], s.y_train[fit]).predict_proba(X_tab[val])[:, 1]
            aucs.append(roc_auc_score(s.y_train[val], p))
        if aucs and np.mean(aucs) > best_auc:
            best, best_auc = params, float(np.mean(aucs))

    model = make(best).fit(X_tab, s.y_train)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_DIR / f"xgboost_split{s.split_num}.json"))
    return model.predict_proba(X_tab_test)[:, 1]


def env_model_scores(daily: pd.DataFrame, s: SimpleNamespace, cfg: dict) -> np.ndarray:
    from train_env_model import MODEL_FEATURES, fit_model, predict
    feats = build_features(daily, cfg["train_end"])
    model = fit_model(feats[feats["target_date"] <= pd.Timestamp(cfg["train_end"])], MODEL_FEATURES)
    feats = feats.set_index(["Location_Name", "target_date"])
    rows = feats.reindex(list(zip(s.locs_test, pd.to_datetime(s.dates_test))))
    return predict(model, rows, MODEL_FEATURES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrain existing model types without look-ahead.")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--models", nargs="+", default=ALL_MODELS, choices=ALL_MODELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    grid = load_grid(args.dataset_path)
    daily = load_daily(args.dataset_path)
    labeled = load_and_prepare(args.dataset_path, imputation_method="hybrid_adaptive")

    records = []
    for cfg in SPLITS:
        s = build_sequences(grid, cfg)
        print(f"\nSplit {s.split_num}: train={len(s.y_train):,}  test={len(s.y_test):,}", flush=True)
        frame = build_test_frame(labeled, s)
        scores = baseline_scores(labeled, s, frame)

        for name in args.models:
            if name in ("lstm", "gru"):
                scores[name] = train_rnn(s, name)
            elif name == "transformer":
                scores[name] = train_transformer(s)
            elif name == "xgboost":
                scores[name] = train_xgboost(s)
            else:
                scores[name] = env_model_scores(daily, s, cfg)
            print(f"  {name:12s} pooled AUC {roc_auc_score(s.y_test, np.nan_to_num(scores[name], nan=0.5)):.3f}", flush=True)

        for row in score_split(frame, scores):
            row["split"] = s.split_num
            records.append(row)

    summarize(pd.DataFrame(records), RESULTS_DIR, "leakfree")


if __name__ == "__main__":
    main()
