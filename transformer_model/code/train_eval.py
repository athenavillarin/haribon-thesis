"""
Transformer training and evaluation utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from transformer_core import build_model, import_torch


@dataclass
class TrainConfig:
    epochs: int = 40
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    val_ratio: float = 0.2
    patience: int = 8

    d_model: int = 64
    num_heads: int = 4
    num_layers: int = 2
    ff_dim: int = 128
    dropout: float = 0.2


def _compute_classification_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }

    if len(np.unique(y_true)) < 2:
        metrics["auc"] = np.nan
    else:
        metrics["auc"] = float(roc_auc_score(y_true, y_prob))

    return metrics


def train_and_evaluate_split(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    config: TrainConfig,
    random_seed: int = 42,
) -> Dict[str, float]:
    """Train one Transformer model and evaluate on one split."""
    torch, nn = import_torch()

    if len(X_train) < 20 or len(X_test) == 0:
        return {
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "accuracy": np.nan,
            "precision": np.nan,
            "recall": np.nan,
            "f1": np.nan,
            "auc": np.nan,
        }

    torch.manual_seed(random_seed)
    np.random.seed(random_seed)

    split_idx = int(len(X_train) * (1.0 - config.val_ratio))
    split_idx = max(1, min(split_idx, len(X_train) - 1))

    X_tr = X_train[:split_idx]
    y_tr = y_train[:split_idx]
    X_val = X_train[split_idx:]
    y_val = y_train[split_idx:]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = build_model(
        input_dim=X_train.shape[2],
        seq_len=X_train.shape[1],
        d_model=config.d_model,
        num_heads=config.num_heads,
        num_layers=config.num_layers,
        ff_dim=config.ff_dim,
        dropout=config.dropout,
    ).to(device)

    xtr = torch.tensor(X_tr, dtype=torch.float32)
    ytr = torch.tensor(y_tr, dtype=torch.float32)
    xval = torch.tensor(X_val, dtype=torch.float32)
    yval = torch.tensor(y_val, dtype=torch.float32)
    xte = torch.tensor(X_test, dtype=torch.float32)

    train_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(xtr, ytr),
        batch_size=config.batch_size,
        shuffle=False,
    )

    pos_count = float(np.sum(y_tr == 1))
    neg_count = float(np.sum(y_tr == 0))
    if pos_count > 0:
        pos_weight = torch.tensor([neg_count / max(pos_count, 1.0)], dtype=torch.float32, device=device)
    else:
        pos_weight = torch.tensor([1.0], dtype=torch.float32, device=device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    best_state = None
    best_val_loss = float("inf")
    wait = 0

    model.train()
    for _ in range(config.epochs):
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(xval.to(device))
            val_loss = criterion(val_logits, yval.to(device)).item()

        if val_loss < best_val_loss - 1e-5:
            best_val_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= config.patience:
                break
        model.train()

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    with torch.no_grad():
        logits = model(xte.to(device)).detach().cpu().numpy()
        probs = 1.0 / (1.0 + np.exp(-logits))

    metrics = _compute_classification_metrics(y_test, probs)
    metrics.update(
        {
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "positive_rate_test": float(np.mean(y_test)) if len(y_test) > 0 else np.nan,
        }
    )
    return metrics
