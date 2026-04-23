"""
ensemble_strategies.py
======================
Three ensemble combination strategies for the HARIBON Objective 2 ensemble.

All functions take a dict of per-model probability arrays and the true labels,
and return a combined probability array of the same length.

Strategies
----------
soft_vote(probs_dict)
    Simple unweighted mean of all available model probabilities.
    Robust, no training required, works even if only some models are available.

weighted_avg(probs_dict, weights)
    Weighted mean — weight each model by its AUC on this split.
    Weights are provided externally (computed by ensemble_evaluate after each
    model produces its per-split AUC).

stacked(probs_dict, y_train_meta, probs_dict_val)
    Logistic Regression meta-learner.
    - Trained on out-of-fold model predictions from the held-out validation
      segments (splits 1-3), then evaluated on split 4.
    - Over the full 4-split evaluation, this uses a leave-one-out scheme:
      for each target split k, the meta-learner is trained on the remaining
      {1,2,3,4} \ {k} splits.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _stack_probs(probs_dict: Dict[str, np.ndarray]) -> Tuple[np.ndarray, List[str]]:
    """Stack model probability arrays into a matrix, ignoring NaN-only columns."""
    valid_models = [m for m, p in probs_dict.items() if not np.all(np.isnan(p))]
    if not valid_models:
        raise ValueError("All model probability arrays are NaN — cannot form ensemble.")
    matrix = np.column_stack([probs_dict[m] for m in valid_models])  # (N, M)
    return matrix, valid_models


# ---------------------------------------------------------------------------
# Strategy 1: Soft vote (unweighted mean)
# ---------------------------------------------------------------------------

def soft_vote(probs_dict: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Unweighted mean of all model probability outputs.

    NaN values within a sample (from failed models) are ignored via nanmean,
    so the ensemble still produces a valid probability even if one model fails.
    """
    matrix, _ = _stack_probs(probs_dict)
    return np.nanmean(matrix, axis=1).astype(np.float32)


# ---------------------------------------------------------------------------
# Strategy 2: Weighted average (AUC-weighted)
# ---------------------------------------------------------------------------

def weighted_avg(
    probs_dict: Dict[str, np.ndarray],
    weights: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Weighted mean of model probabilities.

    Parameters
    ----------
    probs_dict : dict of model_name → probability array
    weights    : dict of model_name → weight (e.g. per-split AUC score).
                 Missing or NaN weights default to equal weight.
                 Negative weights are clipped to 0.
    """
    matrix, valid_models = _stack_probs(probs_dict)

    if weights is None:
        w = np.ones(len(valid_models), dtype=np.float64)
    else:
        w = np.array(
            [max(0.0, float(weights.get(m, 1.0)) if not np.isnan(weights.get(m, 1.0)) else 1.0)
             for m in valid_models],
            dtype=np.float64,
        )

    w_sum = w.sum()
    if w_sum == 0:
        w = np.ones_like(w)
        w_sum = w.sum()

    w_norm = w / w_sum
    combined = (matrix * w_norm).sum(axis=1)
    return combined.astype(np.float32)


# ---------------------------------------------------------------------------
# Strategy 3: Stacking (LogisticRegression meta-learner)
# ---------------------------------------------------------------------------

def build_stacking_meta_features(
    all_split_probs: List[Dict[str, np.ndarray]],
) -> List[np.ndarray]:
    """
    Build meta-feature matrices for each split using leave-one-out.

    For split k → meta-learner is trained on combined data from all OTHER splits,
    then predicts on split k.

    Parameters
    ----------
    all_split_probs : list of probs_dict, one per split (length = n_splits)

    Returns
    -------
    meta_probs : list of 1-D arrays (one per split), length = n_splits
                 Each array contains the meta-learner's calibrated probability
                 for the corresponding split's test set.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    n_splits = len(all_split_probs)

    # Determine consistent model ordering
    base_models = sorted({m for pd_ in all_split_probs for m in pd_.keys()})

    def _to_matrix(pd_: Dict[str, np.ndarray]) -> np.ndarray:
        cols = []
        for m in base_models:
            col = pd_.get(m, np.full(next(iter(pd_.values())).shape, np.nan))
            cols.append(col)
        mat = np.column_stack(cols)
        # Replace NaN with column median
        for j in range(mat.shape[1]):
            nans = np.isnan(mat[:, j])
            if nans.any():
                med = np.nanmedian(mat[:, j])
                mat[nans, j] = med if not np.isnan(med) else 0.5
        return mat.astype(np.float32)

    # Retrieve y_test for each split — stored in all_split_probs as side-channel
    # (caller is expected to pass y arrays via the wrapper in run_ensemble.py)
    raise NotImplementedError(
        "Use stacked_from_splits() which takes y_test arrays explicitly."
    )


def stacked(
    target_split_idx: int,
    all_split_probs: List[Dict[str, np.ndarray]],
    all_y_test: List[np.ndarray],
) -> np.ndarray:
    """
    Leave-one-out stacking meta-learner.

    Trains a LogisticRegression on model probabilities from all splits EXCEPT
    target_split_idx, then predicts on target_split_idx.

    Parameters
    ----------
    target_split_idx : 0-based index of the split to predict (test split)
    all_split_probs  : list[dict] — one probs_dict per split
    all_y_test       : list[np.ndarray] — ground-truth labels per split

    Returns
    -------
    1-D float32 array of meta-learner probabilities for the target split.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    base_models = sorted({m for pd_ in all_split_probs for m in pd_.keys()})

    def _to_matrix(pd_: Dict[str, np.ndarray], n_expected: int) -> np.ndarray:
        cols = []
        for m in base_models:
            if m in pd_:
                col = pd_[m].copy()
            else:
                col = np.full(n_expected, 0.5, dtype=np.float32)
            cols.append(col)
        mat = np.column_stack(cols).astype(np.float32)
        for j in range(mat.shape[1]):
            nans = np.isnan(mat[:, j])
            if nans.any():
                med = float(np.nanmedian(mat[:, j]))
                mat[nans, j] = med if not np.isnan(med) else 0.5
        return mat

    # Build training data from all splits except target
    train_X_parts, train_y_parts = [], []
    for i, (pd_, yt) in enumerate(zip(all_split_probs, all_y_test)):
        if i == target_split_idx:
            continue
        mat = _to_matrix(pd_, len(yt))
        train_X_parts.append(mat)
        train_y_parts.append(yt)

    if not train_X_parts:
        # Only 1 split — cannot train meta-learner, fall back to soft vote
        return soft_vote(all_split_probs[target_split_idx])

    X_meta_train = np.concatenate(train_X_parts, axis=0)
    y_meta_train = np.concatenate(train_y_parts, axis=0)

    n_test = len(all_y_test[target_split_idx])
    X_meta_test = _to_matrix(all_split_probs[target_split_idx], n_test)

    scaler = StandardScaler()
    X_meta_train = scaler.fit_transform(X_meta_train)
    X_meta_test  = scaler.transform(X_meta_test)

    # Use L2 logistic regression — calibrated, handles imbalance
    pos = int(y_meta_train.sum())
    neg = int(len(y_meta_train) - pos)
    class_weight = "balanced" if pos > 0 and neg > 0 else None

    meta_clf = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight=class_weight,
        random_state=42,
        solver="lbfgs",
    )

    if len(np.unique(y_meta_train)) < 2:
        # Only one class in meta-train → fall back to soft vote
        return soft_vote(all_split_probs[target_split_idx])

    meta_clf.fit(X_meta_train, y_meta_train)
    probs = meta_clf.predict_proba(X_meta_test)[:, 1]
    return probs.astype(np.float32)


# ---------------------------------------------------------------------------
# Apply all strategies — convenience wrapper
# ---------------------------------------------------------------------------

def apply_all_strategies(
    probs_dict: Dict[str, np.ndarray],
    auc_weights: Optional[Dict[str, float]] = None,
    stacked_probs: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    """
    Apply all 3 ensemble strategies to a single split's probability dict.

    Parameters
    ----------
    probs_dict    : model → probability array for this split
    auc_weights   : model → AUC weight for this split (for weighted_avg)
    stacked_probs : pre-computed stacked probabilities (from stacked())
                    — because stacking needs cross-split data, it is computed
                    separately in run_ensemble.py and passed in here.

    Returns
    -------
    dict: strategy_name → combined probability array
    """
    out: Dict[str, np.ndarray] = {}
    out["soft_vote"]    = soft_vote(probs_dict)
    out["weighted_avg"] = weighted_avg(probs_dict, auc_weights)
    if stacked_probs is not None:
        out["stacked"] = stacked_probs
    return out
