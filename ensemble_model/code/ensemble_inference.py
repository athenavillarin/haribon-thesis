"""
ensemble_inference.py
=====================
Per-model probability generation for the ensemble pipeline.

Each predict_* function takes a SplitData (already imputed & scaled) and
returns a 1-D float32 numpy array of predicted probabilities for the test set.

Functions
---------
predict_lstm(split, model_dir)       — Keras LSTM (saved weights)
predict_gru(split, model_dir)        — Keras GRU  (saved weights)
predict_transformer(split, model_dir) — PyTorch Transformer (per-split saved .pt)
predict_xgboost(split, model_dir)    — XGBoost (saved JSON model, re-fit per split)
predict_all(split, ...)              — convenience wrapper returning dict of all 4
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Optional

import numpy as np

warnings.filterwarnings("ignore")

_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parent.parent

# Default model paths
DEFAULT_LSTM_MODEL    = _ROOT / "lstm"           / "saved_model" / "haribon_lstm_risk.keras"
DEFAULT_LSTM_SCALER   = _ROOT / "lstm"           / "saved_model" / "feature_scaler.joblib"
DEFAULT_GRU_MODEL     = _ROOT / "gru"            / "saved_model" / "haribon_gru_risk.keras"
DEFAULT_GRU_SCALER    = _ROOT / "gru"            / "saved_model" / "feature_scaler.joblib"
DEFAULT_XGBOOST_MODEL = _ROOT / "xgboost_model"  / "results"     / "best_xgboost_model.json"
DEFAULT_TRANSFORMER_SAVED_DIR = _ROOT / "transformer_model" / "saved_model"


# ---------------------------------------------------------------------------
# LSTM
# ---------------------------------------------------------------------------

def predict_lstm(
    split_data,
    model_path: Path = DEFAULT_LSTM_MODEL,
    scaler_path: Path = DEFAULT_LSTM_SCALER,
) -> np.ndarray:
    """
    Load saved LSTM model and produce test-set probabilities.

    The LSTM was trained with its own MinMaxScaler saved alongside the model.
    We use that scaler (not the ensemble-level scaler) to match training
    preprocessing exactly.
    """
    import joblib
    import tensorflow as tf  # noqa: F401  # triggers GPU setup

    model = tf.keras.models.load_model(str(model_path), compile=False)
    scaler = joblib.load(str(scaler_path))

    X_test = split_data.X_seq_test  # (N, LOOKBACK, n_feat)
    if X_test.shape[0] == 0:
        return np.empty((0,), dtype=np.float32)

    n, L, f = X_test.shape
    X_flat = X_test.reshape(-1, f)
    X_scaled = scaler.transform(X_flat).reshape(n, L, f).astype(np.float32)

    probs = model.predict(X_scaled, verbose=0).flatten()
    return probs.astype(np.float32)


# ---------------------------------------------------------------------------
# GRU
# ---------------------------------------------------------------------------

def predict_gru(
    split_data,
    model_path: Path = DEFAULT_GRU_MODEL,
    scaler_path: Path = DEFAULT_GRU_SCALER,
) -> np.ndarray:
    """Load saved GRU model and produce test-set probabilities."""
    import joblib
    import tensorflow as tf  # noqa: F401

    # Compatibility shim: Keras 3.x added 'quantization_config' to Dense's
    # serialised config; monkey-patch from_config so older builds can load it.
    _orig_dense_from_config = tf.keras.layers.Dense.from_config.__func__

    @classmethod  # type: ignore[misc]
    def _safe_dense_from_config(cls, config):
        config = dict(config)
        config.pop("quantization_config", None)
        return _orig_dense_from_config(cls, config)

    tf.keras.layers.Dense.from_config = _safe_dense_from_config
    try:
        model = tf.keras.models.load_model(str(model_path), compile=False)
    finally:
        # Restore original method regardless of success/failure
        tf.keras.layers.Dense.from_config = classmethod(_orig_dense_from_config)

    scaler = joblib.load(str(scaler_path))

    X_test = split_data.X_seq_test
    if X_test.shape[0] == 0:
        return np.empty((0,), dtype=np.float32)

    n, L, f = X_test.shape
    X_flat = X_test.reshape(-1, f)
    X_scaled = scaler.transform(X_flat).reshape(n, L, f).astype(np.float32)

    probs = model.predict(X_scaled, verbose=0).flatten()
    return probs.astype(np.float32)


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

def predict_transformer(
    split_data,
    saved_dir: Path = DEFAULT_TRANSFORMER_SAVED_DIR,
    scenario: str = "native_masking",
    fallback_retrain: bool = True,
) -> np.ndarray:
    """
    Load per-split saved Transformer weights (.pt) and produce probabilities.

    If no saved weights exist (e.g. run_transformer.py has not been run yet)
    and fallback_retrain=True, the Transformer is re-trained on-the-fly for
    this split — identical to the original run_transformer.py behaviour.
    """
    import sys
    transformer_code = _ROOT / "transformer_model" / "code"
    if str(transformer_code) not in sys.path:
        sys.path.insert(0, str(transformer_code))

    from transformer_core import build_model, import_torch  # type: ignore
    from train_eval import TrainConfig  # type: ignore

    torch, nn = import_torch()

    X_train = split_data.X_seq_train
    X_test  = split_data.X_seq_test

    if X_test.shape[0] == 0:
        return np.empty((0,), dtype=np.float32)

    # Normalise using train statistics (matches native_masking scenario)
    if X_train.shape[0] > 0:
        mean = np.nanmean(X_train, axis=(0, 1), keepdims=True)
        std  = np.nanstd(X_train,  axis=(0, 1), keepdims=True)
        std  = np.where(std < 1e-8, 1.0, std)
        X_train_n = np.nan_to_num((X_train - mean) / std, nan=0.0)
        X_test_n  = np.nan_to_num((X_test  - mean) / std, nan=0.0)
    else:
        X_train_n = X_train
        X_test_n  = X_test

    input_dim = X_test_n.shape[2]
    seq_len   = X_test_n.shape[1]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = TrainConfig()

    model = build_model(
        input_dim=input_dim,
        seq_len=seq_len,
        d_model=cfg.d_model,
        num_heads=cfg.num_heads,
        num_layers=cfg.num_layers,
        ff_dim=cfg.ff_dim,
        dropout=cfg.dropout,
    ).to(device)

    # Try loading saved weights first
    weights_path = saved_dir / f"transformer_{scenario}_split{split_data.split_num}.pt"
    loaded_from_file = False
    if weights_path.exists():
        try:
            state = torch.load(str(weights_path), map_location=device, weights_only=True)
            model.load_state_dict(state)
            loaded_from_file = True
        except (RuntimeError, Exception):
            # Shape mismatch or other incompatibility — fall through to retrain
            pass
    if not loaded_from_file and fallback_retrain and X_train_n.shape[0] >= 20:
        # Re-train on-the-fly (same logic as train_eval.train_and_evaluate_split)
        _train_transformer_inplace(model, X_train_n, split_data.y_train, cfg, device, torch, nn)
        # Save weights for future runs (using an ensemble-specific path to avoid
        # overwriting the transformer benchmark weights)
        ensemble_weights_dir = saved_dir.parent.parent / "ensemble_model" / "saved_model"
        ensemble_weights_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), str(ensemble_weights_dir / weights_path.name))
    elif not loaded_from_file:
        # Not enough data or no weights — return uniform 0.5
        return np.full(X_test_n.shape[0], 0.5, dtype=np.float32)

    model.eval()
    xte = torch.tensor(X_test_n, dtype=torch.float32).to(device)
    with torch.no_grad():
        logits = model(xte).detach().cpu().numpy()
    probs = 1.0 / (1.0 + np.exp(-logits))
    return probs.astype(np.float32)


def _train_transformer_inplace(model, X_train, y_train, cfg, device, torch, nn):
    """Minimal training loop (mirrors train_eval.train_and_evaluate_split)."""
    split_idx = max(1, int(len(X_train) * 0.8))
    X_tr, y_tr = X_train[:split_idx], y_train[:split_idx]
    X_val, y_val = X_train[split_idx:], y_train[split_idx:]

    pos_count = float(np.sum(y_tr == 1))
    neg_count = float(np.sum(y_tr == 0))
    pos_weight = torch.tensor([neg_count / max(pos_count, 1.0)], dtype=torch.float32, device=device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    xtr = torch.tensor(X_tr,  dtype=torch.float32)
    ytr = torch.tensor(y_tr,  dtype=torch.float32)
    xval = torch.tensor(X_val, dtype=torch.float32)
    yval = torch.tensor(y_val, dtype=torch.float32)

    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(xtr, ytr),
        batch_size=cfg.batch_size, shuffle=False,
    )

    best_state, best_loss, wait = None, float("inf"), 0
    model.train()
    for _ in range(cfg.epochs):
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            vl = criterion(model(xval.to(device)), yval.to(device)).item()
        if vl < best_loss - 1e-5:
            best_loss = vl
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= cfg.patience:
                break
        model.train()

    if best_state is not None:
        model.load_state_dict(best_state)


# ---------------------------------------------------------------------------
# XGBoost
# ---------------------------------------------------------------------------

def predict_xgboost(
    split_data,
    model_path: Path = DEFAULT_XGBOOST_MODEL,
) -> np.ndarray:
    """
    Load best XGBoost hyperparameters and fit on the train slice of this split,
    then predict probabilities on the test slice.

    Re-fitting per split avoids data leakage while reusing the optimised
    hyperparameters found by RandomizedSearchCV on the full dataset.
    """
    from xgboost import XGBClassifier

    X_train = split_data.X_tab_train
    y_train = split_data.y_train
    X_test  = split_data.X_tab_test

    if X_test.shape[0] == 0 or X_train.shape[0] == 0:
        return np.empty((0,), dtype=np.float32)

    # Best hyperparameters from xgboost_model/results/best_parameters.txt
    best_params = dict(
        learning_rate=0.2,
        max_depth=8,
        n_estimators=500,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=5,
        min_child_weight=7,
        gamma=0.2,
        objective="binary:logistic",
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )

    clf = XGBClassifier(**best_params)
    clf.fit(X_train, y_train, verbose=False)
    probs = clf.predict_proba(X_test)[:, 1]
    return probs.astype(np.float32)


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def predict_all(
    split_data,
    lstm_model_path: Path = DEFAULT_LSTM_MODEL,
    lstm_scaler_path: Path = DEFAULT_LSTM_SCALER,
    gru_model_path:  Path = DEFAULT_GRU_MODEL,
    gru_scaler_path: Path = DEFAULT_GRU_SCALER,
    xgboost_model_path: Path = DEFAULT_XGBOOST_MODEL,
    transformer_saved_dir: Path = DEFAULT_TRANSFORMER_SAVED_DIR,
    transformer_scenario: str = "native_masking",
) -> Dict[str, np.ndarray]:
    """
    Run inference for all four models on one split.

    Returns a dict: {"lstm": probs, "gru": probs, "transformer": probs, "xgboost": probs}
    Each value is a 1-D float32 array of predicted probabilities, length = len(y_test).
    """
    probs: Dict[str, np.ndarray] = {}

    print("  [lstm]        ", end="", flush=True)
    try:
        probs["lstm"] = predict_lstm(split_data, lstm_model_path, lstm_scaler_path)
        print(f"OK ({len(probs['lstm'])} samples)")
    except Exception as exc:
        print(f"FAILED: {exc}")
        probs["lstm"] = np.full(len(split_data.y_test), np.nan, dtype=np.float32)

    print("  [gru]         ", end="", flush=True)
    try:
        probs["gru"] = predict_gru(split_data, gru_model_path, gru_scaler_path)
        print(f"OK ({len(probs['gru'])} samples)")
    except Exception as exc:
        print(f"FAILED: {exc}")
        probs["gru"] = np.full(len(split_data.y_test), np.nan, dtype=np.float32)

    print("  [transformer] ", end="", flush=True)
    try:
        probs["transformer"] = predict_transformer(split_data, transformer_saved_dir, transformer_scenario)
        print(f"OK ({len(probs['transformer'])} samples)")
    except Exception as exc:
        print(f"FAILED: {exc}")
        probs["transformer"] = np.full(len(split_data.y_test), np.nan, dtype=np.float32)

    print("  [xgboost]     ", end="", flush=True)
    try:
        probs["xgboost"] = predict_xgboost(split_data, xgboost_model_path)
        print(f"OK ({len(probs['xgboost'])} samples)")
    except Exception as exc:
        print(f"FAILED: {exc}")
        probs["xgboost"] = np.full(len(split_data.y_test), np.nan, dtype=np.float32)

    return probs
