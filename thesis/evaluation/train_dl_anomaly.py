"""
train_dl_anomaly.py
===================
Trains LSTM, GRU and Transformer models on the environment-driven features
(site-relative 30/60/90-day sea temperature and rainfall anomalies, season,
ONI and earlier-year ban history) instead of raw daily values, and scores them
against the baselines and the logistic regression benchmark (env_model).

Each model sees the last LOOKBACK days of features and predicts the next day's
ban status. Training uses the same testing-delay sample weights as env_model
and no class reweighting, so probabilities stay calibrated. Each deep model is
trained with N_SEEDS random starts and the predictions are averaged.

Reported models:
    lstm, gru, transformer   deep models on the new features
    dl_mean                  average of the three deep models
    dl_lr                    average of dl_mean and the logistic regression
    env_model                logistic regression benchmark

Results go to results/dl_anomaly_per_split.csv and dl_anomaly_summary.csv;
every test-day prediction goes to results/dl_anomaly_predictions.csv so other
metrics can be computed without retraining.

Usage:
    cd evaluation
    python train_dl_anomaly.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

_THIS_DIR = Path(__file__).resolve().parent
_THESIS_DIR = _THIS_DIR.parent
for p in (_THESIS_DIR / "env_model", _THESIS_DIR / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from baselines import baseline_scores, build_test_frame, score_split, summarize  # noqa: E402
from ensemble_data import DEFAULT_DATASET_PATH, SPLITS, load_and_prepare  # noqa: E402
from features import build_features, load_daily  # noqa: E402
from train_env_model import MODEL_FEATURES, fit_model, predict  # noqa: E402

RESULTS_DIR = _THIS_DIR / "results"
DL_MODELS = ["lstm", "gru", "transformer"]
LOOKBACK = 30
N_SEEDS = 3
HOLDOUT_DAYS = 365
MAX_EPOCHS = 40
BATCH_SIZE = 128


def feature_scaling(feats: pd.DataFrame, train_end: pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """Mean and standard deviation of each feature over training dates."""
    train = feats.loc[feats["Date"] <= train_end, MODEL_FEATURES]
    return train.mean(), train.std().replace(0, 1)


def standardize(feats: pd.DataFrame, mean: pd.Series, std: pd.Series) -> np.ndarray:
    return ((feats[MODEL_FEATURES].fillna(mean) - mean) / std).to_numpy(dtype=np.float32)


def build_windows(feats: pd.DataFrame, cfg: dict) -> SimpleNamespace:
    """LOOKBACK-day windows of standardized features, each predicting the next day's label."""
    train_end = pd.Timestamp(cfg["train_end"])
    test_start = pd.Timestamp(cfg.get("test_start", train_end + pd.Timedelta(days=1)))
    test_end = pd.Timestamp(cfg.get("test_end", test_start))
    mean, std = feature_scaling(feats, train_end)
    X_all = standardize(feats, mean, std)

    parts = {k: [] for k in ("X_tr", "y_tr", "w_tr", "d_tr", "X_te", "y_te", "d_te", "l_te")}
    for loc, idx in feats.groupby("Location_Name", sort=False).indices.items():
        X = X_all[idx]
        g = feats.iloc[idx]
        y, w, td = g["target"].to_numpy(), g["target_weight"].to_numpy(), g["target_date"].to_numpy()
        for t in range(LOOKBACK - 1, len(g)):
            if np.isnan(y[t]):
                continue
            window = X[t - LOOKBACK + 1: t + 1]
            if td[t] <= np.datetime64(train_end):
                parts["X_tr"].append(window); parts["y_tr"].append(y[t])
                parts["w_tr"].append(w[t]); parts["d_tr"].append(td[t])
            elif np.datetime64(test_start) <= td[t] <= np.datetime64(test_end):
                parts["X_te"].append(window); parts["y_te"].append(y[t])
                parts["d_te"].append(td[t]); parts["l_te"].append(loc)

    return SimpleNamespace(
        split_num=cfg.get("split_num"),
        feature_mean=mean,
        feature_std=std,
        train_end=cfg["train_end"],
        X_train=np.stack(parts["X_tr"]),
        y_train=np.array(parts["y_tr"], dtype=np.float32),
        w_train=np.nan_to_num(np.array(parts["w_tr"], dtype=np.float32), nan=1.0),
        dates_train=np.array(parts["d_tr"]),
        X_test=np.stack(parts["X_te"]) if parts["X_te"] else np.empty((0, LOOKBACK, len(MODEL_FEATURES)), np.float32),
        y_test=np.array(parts["y_te"], dtype=np.int64),
        dates_test=np.array(parts["d_te"]),
        locs_test=np.array(parts["l_te"], dtype=object),
    )


def build_model(kind: str, n_features: int):
    """Small networks: the data hold about 50 ban starts."""
    import tensorflow as tf
    from tensorflow.keras import layers

    inputs = layers.Input(shape=(LOOKBACK, n_features))
    if kind == "lstm":
        x = layers.LSTM(16, kernel_regularizer=tf.keras.regularizers.l2(1e-3))(inputs)
    elif kind == "gru":
        x = layers.GRU(16, kernel_regularizer=tf.keras.regularizers.l2(1e-3))(inputs)
    else:
        x = layers.Dense(32)(inputs)
        positions = layers.Embedding(LOOKBACK, 32)(tf.range(LOOKBACK))
        x = x + positions
        attn = layers.MultiHeadAttention(num_heads=2, key_dim=16, dropout=0.1)(x, x)
        x = layers.LayerNormalization()(x + attn)
        ff = layers.Dense(32, activation="relu")(x)
        x = layers.LayerNormalization()(x + layers.Dense(32)(ff))
        x = x[:, -1, :]
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="binary_crossentropy")
    return model


def fit_dl(s: SimpleNamespace, kind: str, seed: int):
    """Choose the epoch count on the last HOLDOUT_DAYS of training, then refit on the full training period."""
    import tensorflow as tf

    hold = s.dates_train > np.datetime64(pd.Timestamp(s.train_end) - pd.Timedelta(days=HOLDOUT_DAYS))
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(seed)
    model = build_model(kind, s.X_train.shape[2])
    stopper = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    model.fit(s.X_train[~hold], s.y_train[~hold], sample_weight=s.w_train[~hold],
              validation_data=(s.X_train[hold], s.y_train[hold], s.w_train[hold]),
              epochs=MAX_EPOCHS, batch_size=BATCH_SIZE, callbacks=[stopper], verbose=0)
    epochs = max(1, stopper.best_epoch + 1)

    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(seed)
    model = build_model(kind, s.X_train.shape[2])
    model.fit(s.X_train, s.y_train, sample_weight=s.w_train,
              epochs=epochs, batch_size=BATCH_SIZE, verbose=0)
    return model


def train_dl(s: SimpleNamespace, kind: str) -> np.ndarray:
    """Average test predictions of N_SEEDS models."""
    preds = [fit_dl(s, kind, seed).predict(s.X_test, verbose=0).ravel() for seed in range(N_SEEDS)]
    return np.mean(preds, axis=0)


def env_model_scores(feats: pd.DataFrame, s: SimpleNamespace) -> np.ndarray:
    labeled = feats.dropna(subset=["target"])
    model = fit_model(labeled[labeled["target_date"] <= pd.Timestamp(s.train_end)], MODEL_FEATURES)
    rows = labeled.set_index(["Location_Name", "target_date"]).reindex(
        list(zip(s.locs_test, pd.to_datetime(s.dates_test))))
    return predict(model, rows, MODEL_FEATURES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deep models on the environment-driven features.")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--models", nargs="+", default=DL_MODELS, choices=DL_MODELS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    daily = load_daily(args.dataset_path)
    labeled = load_and_prepare(args.dataset_path, imputation_method="hybrid_adaptive")

    records, predictions = [], []
    for cfg in SPLITS:
        feats = build_features(daily, cfg["train_end"], keep_unlabeled=True)
        s = build_windows(feats, cfg)
        print(f"\nSplit {s.split_num}: train={len(s.y_train):,}  test={len(s.y_test):,}", flush=True)
        frame = build_test_frame(labeled, s)
        scores = baseline_scores(labeled, s, frame)
        scores["env_model"] = env_model_scores(feats, s)

        for kind in args.models:
            scores[kind] = train_dl(s, kind)
            print(f"  {kind:12s} pooled AUC {roc_auc_score(s.y_test, scores[kind]):.3f}", flush=True)
        scores["dl_mean"] = np.mean([scores[k] for k in args.models], axis=0)
        scores["dl_lr"] = (scores["dl_mean"] + scores["env_model"]) / 2

        predictions.append(pd.DataFrame({
            "split": s.split_num, "Location_Name": s.locs_test, "target_date": s.dates_test, "y": s.y_test,
            **{name: np.asarray(p, dtype=float) for name, p in scores.items()},
        }))
        for row in score_split(frame, scores):
            row["split"] = s.split_num
            records.append(row)

    pd.concat(predictions).to_csv(RESULTS_DIR / "dl_anomaly_predictions.csv", index=False)
    summarize(pd.DataFrame(records), RESULTS_DIR, "dl_anomaly")


if __name__ == "__main__":
    main()
