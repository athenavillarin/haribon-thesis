"""
shap_ensemble.py
================
SHAP values for the deployed Ensemble (artifacts/best_model/env_model/):
the LSTM, GRU and Transformer seeds averaged per type, the three types
averaged, then averaged with the logistic regression.

The whole Ensemble is written as one TensorFlow model on the 30-day input
window, and SHAP values are estimated with expected gradients (the method
behind shap.GradientExplainer). Each feature's value is summed over the 30 days,
so it is in probability units and the values for a day add up to that day's
prediction minus the average prediction.

Usage:
    cd env_model
    python shap_ensemble.py
    python shap_ensemble.py --plot-only   # redraw from saved values

Output:
    results/shap_ensemble_bar.png
    results/shap_ensemble_beeswarm.png
    results/shap_ensemble_importance.csv
    results/shap_ensemble_values.npz   (SHAP values, for redrawing with --plot-only)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

_THIS_DIR = Path(__file__).resolve().parent
for p in (_THIS_DIR.parent / "evaluation", _THIS_DIR.parent / "ensemble_model" / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ensemble_data import DEFAULT_DATASET_PATH  # noqa: E402
from features import build_features, load_daily  # noqa: E402
from train_dl_anomaly import LOOKBACK, build_model, build_windows  # noqa: E402

BUNDLE_PATH = _THIS_DIR.parents[1] / "artifacts" / "best_model" / "env_model" / "env_model.json"
RESULTS_DIR = _THIS_DIR / "results"
N_EXPLAIN = 2000
N_BACKGROUND = 300
N_DRAWS = 200
SEED = 0

LABELS = {
    "thetao_roll30": "Sea temp. anomaly (30-day)",
    "thetao_roll60": "Sea temp. anomaly (60-day)",
    "thetao_roll90": "Sea temp. anomaly (90-day)",
    "precip_mm_day_roll30": "Rainfall anomaly (30-day)",
    "precip_mm_day_roll60": "Rainfall anomaly (60-day)",
    "precip_mm_day_roll90": "Rainfall anomaly (90-day)",
    "doy_sin": "Season (day-of-year sine)",
    "doy_cos": "Season (day-of-year cosine)",
    "oni": "ENSO index (ONI, 3-month lag)",
    "clim_rate": "Site ban rate for this month (earlier years)",
    "site_rate_365": "Site ban rate, previous year",
}


def ensemble_model(bundle: dict):
    """The deployed Ensemble as one Keras model on standardized 30-day windows."""
    import tensorflow as tf
    from tensorflow.keras import layers

    spec = bundle["deep_models"]
    n_features = len(bundle["features"])
    inputs = layers.Input(shape=(LOOKBACK, n_features))

    by_kind = []
    for kind, files in spec["weights"].items():
        seeds = []
        for name in files:
            model = build_model(kind, n_features)
            model.load_weights(BUNDLE_PATH.parent / name)
            seeds.append(model(inputs))
        by_kind.append(layers.Average()(seeds))
    deep = layers.Average()(by_kind)

    # The logistic regression on the last day, rewritten to take the deep models' standardized inputs
    dl_mean, dl_std = np.array(spec["feature_mean"]), np.array(spec["feature_std"])
    lr_mean, lr_scale = np.array(bundle["scaler_mean"]), np.array(bundle["scaler_scale"])
    coef = np.array(bundle["coef"])
    kernel = dl_std * coef / lr_scale
    bias = float(((dl_mean - lr_mean) * coef / lr_scale).sum() + bundle["intercept"])
    last_day = layers.Flatten()(layers.Cropping1D((LOOKBACK - 1, 0))(inputs))
    lr = layers.Dense(1, activation="sigmoid")
    lr_out = lr(last_day)
    lr.set_weights([kernel.reshape(-1, 1).astype(np.float32), np.array([bias], dtype=np.float32)])

    return tf.keras.Model(inputs, layers.Average()([deep, lr_out]))


def expected_gradients(model, X: np.ndarray, background: np.ndarray, draws: int, rng) -> np.ndarray:
    """SHAP values by expected gradients: mean of grad(b + a(x - b)) * (x - b) over background b and a in [0, 1]."""
    import tensorflow as tf

    out = np.zeros_like(X)
    for i in range(0, len(X), 50):
        x = X[i:i + 50]
        total = np.zeros_like(x)
        for _ in range(draws // 10):
            b = background[rng.integers(0, len(background), size=(10, len(x)))]
            a = rng.uniform(size=(10, len(x), 1, 1)).astype(np.float32)
            point = tf.constant((b + a * (x[None] - b)).reshape(-1, *x.shape[1:]))
            with tf.GradientTape() as tape:
                tape.watch(point)
                pred = model(point, training=False)
            grad = tape.gradient(pred, point).numpy().reshape(10, *x.shape)
            total += (grad * (x[None] - b)).sum(axis=0)
        out[i:i + 50] = total / (draws // 10 * 10)
    return out


def main() -> None:
    import tensorflow as tf

    tf.keras.utils.set_random_seed(SEED)
    rng = np.random.default_rng(SEED)
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    features = bundle["features"]

    daily = load_daily(DEFAULT_DATASET_PATH)
    feats = build_features(daily, bundle["trained_through"], keep_unlabeled=True)
    s = build_windows(feats, {"train_end": bundle["trained_through"]})
    assert np.allclose(s.feature_mean.to_numpy(), bundle["deep_models"]["feature_mean"])

    model = ensemble_model(bundle)
    X = s.X_train[rng.choice(len(s.X_train), size=N_EXPLAIN, replace=False)]
    background = s.X_train[rng.choice(len(s.X_train), size=N_BACKGROUND, replace=False)]

    window_shap = expected_gradients(model, X, background, N_DRAWS, rng)
    values = window_shap.sum(axis=1)
    pred = model.predict(X, verbose=0).ravel()
    base = float(model.predict(background, verbose=0).mean())
    gap = np.abs(values.sum(axis=1) - (pred - base))
    print(f"Average prediction {base:.3f}; SHAP additivity error mean {gap.mean():.4f}, max {gap.max():.4f}")

    shown = (X[:, -1, :] * s.feature_std.to_numpy() + s.feature_mean.to_numpy()).astype(float)
    names = [LABELS[f] for f in features]

    importance = pd.DataFrame({"feature": features, "label": names,
                               "mean_abs_shap": np.abs(values).mean(axis=0)}).sort_values("mean_abs_shap", ascending=False)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    importance.to_csv(RESULTS_DIR / "shap_ensemble_importance.csv", index=False)
    print(importance.to_string(index=False))

    np.savez(RESULTS_DIR / "shap_ensemble_values.npz", values=values, shown=shown, names=np.array(names))
    plot(values, shown, names)
    print(f"Saved figures to {RESULTS_DIR}")


def plot(values: np.ndarray, shown: np.ndarray, names: list[str]) -> None:
    import shap

    shap.summary_plot(values, shown, feature_names=names, plot_type="bar", show=False)
    plt.xlabel("Mean |SHAP value|")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "shap_ensemble_bar.png", dpi=200, bbox_inches="tight")
    plt.close()

    shap.summary_plot(values, shown, feature_names=names, show=False)
    plt.xlabel("SHAP value (impact on the ban probability)")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "shap_ensemble_beeswarm.png", dpi=200, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        saved = np.load(RESULTS_DIR / "shap_ensemble_values.npz")
        plot(saved["values"], saved["shown"], list(saved["names"]))
    else:
        main()
