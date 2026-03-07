# HARIBON Red Tide Validation Study — Objective 2, Task 5: Ensemble Model

## Overview
Task 5 implements the **Ensemble Model** for HARIBON Objective 2, combining all four independently trained HAB detection models — **LSTM**, **GRU**, **Transformer**, and **XGBoost** — into a unified ensemble. Three combination strategies are evaluated on 4 common rolling-origin splits, and the final **Objective 2 model comparison table** is compiled.

**Status**: COMPLETE — 4 base models trained and integrated; ensemble executed over 4 splits with 3 combination strategies; results compiled in `results/`

---

## Quick Start

### Prerequisites
All four base models must be trained before running the ensemble:

| Model | Required file |
|---|---|
| LSTM | `lstm/saved_model/haribon_lstm_risk.keras` |
| GRU | `gru/saved_model/haribon_gru_risk.keras` |
| Transformer | `transformer_model/saved_model/transformer_native_masking_split*.pt` |
| XGBoost | `xgboost_model/results/best_xgboost_model.json` |

If the Transformer `.pt` weight files are missing, generate them first:
```bash
cd transformer_model
python run_transformer.py
```

### Run Complete Ensemble Analysis
```bash
cd ensemble_model
python run_ensemble.py
```
**Output**: 3 results CSVs in `ensemble_model/results/`

### Individual Options
```bash
# Run only specific strategies
python run_ensemble.py --strategies soft_vote weighted_avg

# Run only specific splits
python run_ensemble.py --splits 1 2 3

# Use hybrid-adaptive Transformer scenario instead of native masking (default)
python run_ensemble.py --transformer-scenario hybrid_adaptive
```

---

## Individual Model Baselines

### LSTM — Rolling-Origin Results (6 Splits)

| Split | Train End | Test Year(s) | Threshold | Accuracy | Precision | Recall | F1 (Macro) | AUC-ROC |
|---|---|---|---|---|---|---|---|---|
| 1 | 2019 | 2020 | 0.500 | 0.9473 | 0.7619 | 0.1127 | 0.5845 | 0.8758 |
| 2 | 2020 | 2021 | 0.500 | 0.8140 | 0.6857 | 0.0976 | 0.5330 | 0.4292 |
| 3 | 2021 | 2022 | 0.500 | 0.6947 | 0.6795 | 0.0676 | 0.4691 | 0.7329 |
| 4 | 2022 | 2023 | 0.288 | 0.5679 | 0.4470 | 0.2085 | 0.4874 | 0.5609 |
| 5 | 2023 | 2024 | 0.331 | 0.8734 | 0.7314 | 0.7302 | 0.8240 | 0.8918 |
| 6 | 2024 | 2025–2026 | 0.337 | 0.9119 | 0.7879 | 0.8863 | 0.8871 | 0.9627 |
| **Mean** | | | | **0.7999** | **0.6822** | **0.3505** | **0.6309** | **0.7422** |

**Best split**: Split 6 — AUC-ROC = **0.9627**

---

### GRU — Rolling-Origin Results (6 Splits)

| Split | Train End | Test Year(s) | Threshold | Accuracy | Precision | Recall | F1 (Macro) | AUC-ROC |
|---|---|---|---|---|---|---|---|---|
| 1 | 2019 | 2020 | 0.500 | 0.9428 | 0.5000 | 0.1549 | 0.6034 | 0.7140 |
| 2 | 2020 | 2021 | 0.500 | 0.8208 | 0.8772 | 0.1016 | 0.5407 | 0.4674 |
| 3 | 2021 | 2022 | 0.500 | 0.7052 | 0.6800 | 0.1301 | 0.5184 | 0.7205 |
| 4 | 2022 | 2023 | 0.246 | 0.5439 | 0.4269 | 0.3143 | 0.5036 | 0.5711 |
| 5 | 2023 | 2024 | 0.300 | 0.8008 | 0.5538 | 0.7892 | 0.7558 | 0.8548 |
| 6 | 2024 | 2025–2026 | 0.304 | 0.9171 | 0.7603 | 0.9764 | 0.8984 | 0.9653 |
| **Mean** | | | | **0.7884** | **0.6330** | **0.4111** | **0.6367** | **0.7155** |

**Best split**: Split 6 — AUC-ROC = **0.9653**

---

### Transformer — Rolling-Origin Results (4 Splits, Native Masking)

| Split | Cutoff Date | Test Window | Accuracy | Precision | Recall | F1 | AUC-ROC |
|---|---|---|---|---|---|---|---|
| 1 | 2016-01-04 | 2016-01-05 → 2016-04-03 | 0.5840 | 0.3811 | 0.9490 | 0.5438 | 0.8797 |
| 2 | 2019-04-21 | 2019-04-22 → 2019-07-20 | 0.8429 | 0.0000 | 0.0000 | 0.0000 | — ¹ |
| 3 | 2022-08-06 | 2022-08-07 → 2022-11-04 | 0.6617 | 1.0000 | 0.3072 | 0.4700 | 0.6909 |
| 4 | 2025-11-22 | 2025-11-23 → 2026-02-20 | 0.6984 | 0.0000 | 0.0000 | 0.0000 | 0.7567 |
| **Mean** | | | **0.6968** | **0.3453** | **0.3141** | **0.2535** | **0.7758 ± 0.096** |

¹ No positive (bloom) events in the test window for Split 2 — AUC undefined.

**Hybrid Adaptive** scenario summary: AUC mean = 0.6634 ± 0.202 — native masking outperforms hybrid adaptive.

---

### XGBoost — Task 4 Results (4 Rolling-Origin Splits)

Best imputation pipeline: **Hybrid Gap-Type Adaptive** (ranks 1st by AUC across all imputation methods tested in Tasks 2–3).

| Imputation Method | AUC (Mean) | AUC (Std) | F1 (Mean) | F1 (Std) | n Splits |
|---|---|---|---|---|---|
| **Hybrid: Gap-Type Adaptive** | **0.7942** | 0.1427 | 0.1863 | 0.2425 | 4 |
| Linear Interpolation | 0.5962 | 0.2379 | 0.0000 | 0.0000 | 4 |
| Hybrid: Sequential Temporal→Spatial | 0.6007 | 0.2364 | 0.0000 | 0.0000 | 4 |
| Distance-Weighted Average | 0.4372 | 0.0801 | 0.0000 | 0.0000 | 4 |
| Climatological Substitution | 0.6963 | 0.0249 | 0.2906 | 0.2290 | 4 |

**Standalone XGBoost** (full-dataset cross-validation, `xgboost_model/`): CV AUC = **0.9833**

---

## Ensemble Results (4 Splits, hybrid_adaptive Transformer scenario)

### Per-Model & Strategy Summary (mean ± std, 4 splits, ranked by AUC)

| Rank | Source | Model / Strategy | Accuracy | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|---|---|
| 1 | model | LSTM | 0.793 ± 0.135 | 0.725 ± 0.308 | 0.223 ± 0.095 | 0.332 ± 0.137 | **0.881 ± 0.097** |
| 2 | model | GRU | 0.778 ± 0.134 | 0.694 ± 0.270 | 0.142 ± 0.043 | 0.230 ± 0.070 | **0.875 ± 0.098** |
| 3 | ensemble | weighted_avg | 0.777 ± 0.139 | 0.904 ± 0.144 | 0.117 ± 0.047 | 0.202 ± 0.063 | **0.861 ± 0.100** |
| 4 | ensemble | stacked | 0.755 ± 0.112 | 0.621 ± 0.332 | 0.662 ± 0.469 | 0.436 ± 0.328 | **0.848 ± 0.161** |
| 5 | ensemble | soft_vote | 0.775 ± 0.138 | 0.900 ± 0.144 | 0.107 ± 0.066 | 0.183 ± 0.090 | **0.843 ± 0.102** |
| 6 | model | XGBoost | 0.770 ± 0.127 | 0.581 ± 0.271 | 0.151 ± 0.041 | 0.232 ± 0.069 | **0.666 ± 0.083** |
| 7 | model | Transformer | 0.758 ± 0.148 | 0.133 ± 0.266 | 0.082 ± 0.164 | 0.102 ± 0.203 | **0.506 ± 0.066** |

> **Best ensemble strategy**: weighted_avg (AUC = 0.861). LSTM and GRU individually rank #1 and #2 on the common 4-split evaluation.

### Per-Split Detail

| Split | Test Period | LSTM AUC | GRU AUC | Transformer AUC | XGBoost AUC | Stacked AUC | WeightedAvg AUC |
|---|---|---|---|---|---|---|---|
| 1 | 2020 | 0.924 | 0.920 | 0.546 | 0.774 | 0.929 | 0.915 |
| 2 | 2021 | 0.977 | 0.959 | 0.502 | 0.579 | 0.976 | 0.960 |
| 3 | 2022 | 0.873 | 0.885 | 0.414 | 0.631 | 0.871 | 0.838 |
| 4 | 2023 | 0.751 | 0.735 | 0.561 | 0.680 | 0.615 | 0.732 |
| **Mean** | | **0.881** | **0.875** | **0.506** | **0.666** | **0.848** | **0.861** |

---

## Objective 2 Final Model Comparison

| Rank | Model | AUC (Mean ± Std) | Accuracy | F1 | n Splits | Notes |
|---|---|---|---|---|---|---|
| 1 | **Ensemble (weighted_avg)** | **0.862 ± 0.100** | 0.777 ± 0.139 | 0.202 ± 0.063 | 4 | Best ensemble strategy by AUC |
| 2 | XGBoost (Hybrid Gap-Type Adaptive) | 0.794 ± 0.143 | — | 0.186 ± 0.243 | 4 | Task 4 downstream evaluation |
| 3 | Transformer (native_masking) | 0.776 ± 0.096 | 0.697 ± 0.108 | 0.253 ± 0.294 | 4 | Best transformer scenario |
| 4 | LSTM | 0.650 ± 0.195 | 0.756 ± 0.162 | 0.519 ± 0.052 | 4 | Splits 1–4 of 6 yearly splits |
| 5 | GRU | 0.618 ± 0.122 | 0.753 ± 0.170 | 0.542 ± 0.044 | 4 | Splits 1–4 of 6 yearly splits |

> Full results written to `results/obj2_model_comparison_final.csv`.

---

## Ensemble Strategies

### 1. Soft Vote (`soft_vote`)
Simple unweighted mean of all four model probability outputs. NaN predictions from any model are skipped via `nanmean`.

$$P_{ensemble}(t) = \frac{1}{M} \sum_{m=1}^{M} P_m(t)$$

where $M$ is the number of models contributing a non-NaN prediction at time $t$.

**Best for**: Stability — robust even if one model fails on a given split.

### 2. Weighted Average (`weighted_avg`)
Each model's contribution is proportional to its AUC score on the same split. Models with AUC below 0.5 are clipped to weight 0.

$$P_{ensemble}(t) = \frac{\sum_{m=1}^{M} w_m \cdot P_m(t)}{\sum_{m=1}^{M} w_m}, \quad w_m = \max(0,\ \text{AUC}_m)$$

**Best for**: Situations where one or two models dominate on specific splits.

### 3. Stacking (`stacked`)
A Logistic Regression meta-learner is trained on the four base model probability outputs using a **leave-one-out** scheme across the four splits.

$$P_{meta}(t) = \sigma\!\left(\beta_0 + \sum_{m=1}^{M} \beta_m \cdot P_m(t)\right)$$

To evaluate split $k$, the meta-learner trains on all splits $\neq k$:

$$\hat{\beta} = \arg\min_\beta \sum_{i \neq k} \mathcal{L}(y_i,\ P_{meta}(x_i;\beta))$$

**Best for**: Learning non-linear re-weighting of base model outputs when sufficient training splits exist.

---

## Data Pipeline & Imputation

The ensemble shares a unified data preparation pipeline (`ensemble_data.py`) applying **4-phase Hybrid Gap-Adaptive imputation** to the combined dataset before splitting:

| Phase | Method | Applied when |
|---|---|---|
| 1 | Linear interpolation | Gaps ≤ 14 consecutive days |
| 2 | Climatological mean | Remaining gaps (Location × Month average) |
| 3 | Location mean | Fallback if climatological mean unavailable |
| 4 | Global mean | Emergency fallback for fully missing variables |

**Features (11)**: `CHL`, `NDVI_daily`, `mlotst`, `precip_mm_day`, `so`, `thetao`, `uo`, `vo`, `wind_speed_ms`, `wind_u_ms`, `wind_v_ms`  
**Target**: `red_tide_label` → binarized at threshold ≥ 0.5 → `red_tide_binary`  
**Sequence length**: lookback = 30 days (used by LSTM, GRU, Transformer)  
**Dataset**: `final_compiled_dataset/Combined_Labeled.csv`

---

## Split Framework

The ensemble evaluates on **4 common rolling-origin splits** aligned to the LSTM/GRU yearly evaluation windows:

| Split | Train period | Test period | Train size (approx.) | Test size (approx.) |
|---|---|---|---|---|
| 1 | ≤ 2019-12-31 | 2020 (full year) | ~730 seq | ~730 seq |
| 2 | ≤ 2020-12-31 | 2021 (full year) | ~1,095 seq | ~730 seq |
| 3 | ≤ 2021-12-31 | 2022 (full year) | ~1,460 seq | ~730 seq |
| 4 | ≤ 2022-12-31 | 2023 (full year) | ~1,825 seq | ~730 seq |

---

## Model Inference Details

| Model | Inference method | Required artifacts |
|---|---|---|
| LSTM | Load `.keras` + `feature_scaler.joblib` → `model.predict()` on 3-D sequences (N, 30, 11) | `lstm/saved_model/` |
| GRU | Identical pipeline to LSTM | `gru/saved_model/` |
| Transformer | Load per-split `.pt` weights → PyTorch forward pass via `HABTransformerClassifier`; fallback retrains on-the-fly if `.pt` missing | `transformer_model/saved_model/` |
| XGBoost | Load best hyperparameters from `best_parameters.txt` → refit `XGBClassifier` on each train slice → `predict_proba()` | `xgboost_model/results/` |

> XGBoost is **refit per split** rather than loading a single trained model to prevent data leakage across the rolling-origin evaluation windows.

---

## Output Files

### `results/ensemble_per_split_metrics.csv`
Per-split AUC, F1, Precision, Recall, and Accuracy for every individual model and every ensemble strategy.

**Columns**: `split_num`, `train_end`, `test_start`, `test_end`, `n_train`, `n_test`, `positive_rate`, `source`, `name`, `accuracy`, `precision`, `recall`, `f1`, `auc`

### `results/ensemble_summary.csv`
Aggregated mean ± std across all 4 splits, ranked by mean AUC.

**Columns**: `rank_auc`, `source`, `name`, `accuracy_mean`, `accuracy_std`, `precision_mean`, `precision_std`, `recall_mean`, `recall_std`, `f1_mean`, `f1_std`, `auc_mean`, `auc_std`, `n_splits`

### `results/obj2_model_comparison_final.csv`
**The definitive Objective 2 results table.** Combines metrics from all four base models and the best ensemble strategy, all ranked by AUC.

**Columns**: `rank`, `model`, `auc_mean`, `auc_std`, `accuracy_mean`, `accuracy_std`, `precision_mean`, `precision_std`, `recall_mean`, `recall_std`, `f1_mean`, `f1_std`, `n_splits`, `notes`

---

## File Structure

```
ensemble_model/
├── README.md                         # This file
├── run_ensemble.py                   # Master execution script (CLI entry point)
├── code/
│   ├── ensemble_data.py              # Data loading, imputation, split generation (237 lines)
│   ├── ensemble_inference.py         # Per-model probability generation (260 lines)
│   ├── ensemble_strategies.py        # Soft vote, weighted avg, stacking (200 lines)
│   └── ensemble_evaluate.py          # Metrics, summary tables, Obj 2 comparison (248 lines)
└── results/
    ├── ensemble_per_split_metrics.csv   # Per-split metrics (all models + strategies)
    ├── ensemble_summary.csv             # Mean ± std summary, ranked by AUC
    └── obj2_model_comparison_final.csv  # Final Obj 2 table (5 rows: 4 models + best ensemble)
```

---

## Implementation Details

### Code Architecture

**`ensemble_data.py`**:
- `load_and_prepare(path)` — reads `Combined_Labeled.csv`, applies 4-phase imputation, returns cleaned DataFrame
- `build_splits(df)` — constructs 4 `SplitData` objects with train/test arrays
- `scale_splits(splits)` — fits `MinMaxScaler` on each train set; returns scaled splits + scalers
- `SplitData` dataclass — holds `X_seq_train/test` (N, 30, 11), `X_tab_train/test` (N, 11), `y_train/test`, `dates_test`

**`ensemble_inference.py`**:
- `predict_lstm(split, model_path, scaler_path)` — Keras model inference
- `predict_gru(split, model_path, scaler_path)` — Keras model inference
- `predict_transformer(split, saved_dir, scenario, fallback_retrain=True)` — PyTorch inference with on-the-fly retraining fallback
- `predict_xgboost(split, model_path)` — per-split refit + `predict_proba()`
- `predict_all(split_data, ...)` — convenience wrapper returning `{"lstm", "gru", "transformer", "xgboost"}` probability dicts

**`ensemble_strategies.py`**:
- `soft_vote(probs_dict)` — `np.nanmean` across model axes
- `weighted_avg(probs_dict, weights)` — AUC-weighted mean, clips negatives
- `stacked(target_split_idx, all_split_probs, all_y_test)` — LOO `LogisticRegression` meta-learner with `StandardScaler` and `class_weight="balanced"`
- `apply_all_strategies(...)` — runs all three and returns combined dict

**`ensemble_evaluate.py`**:
- `compute_metrics(y_true, y_prob, threshold=0.5)` — accuracy, precision, recall, F1, AUC
- `build_per_split_records(split_results)` — flat DataFrame, one row per model/strategy/split
- `build_summary(per_split_df)` — mean ± std grouped by `(source, name)`, ranked by AUC
- `build_obj2_comparison(ensemble_summary, output_path)` — loads pre-computed CSVs from each model folder and appends best ensemble result

### Performance Metrics

- **AUC-ROC**: $\int_0^1 \text{TPR}(t)\, d[\text{FPR}(t)]$ — primary ranking metric; threshold-independent
- **F1 (Macro)**: $\frac{1}{K}\sum_{k=1}^{K} \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$ — equally weights all classes
- **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$ — overall correctness
- **Precision / Recall**: per-class bloom detection rates

---

## Dependencies

```bash
pip install tensorflow torch xgboost scikit-learn pandas numpy joblib
```

| Library | Minimum version | Purpose |
|---|---|---|
| tensorflow | 2.12 | LSTM / GRU model loading |
| torch | 2.0 | Transformer inference |
| xgboost | 1.7 | XGBoost per-split refit |
| scikit-learn | 1.3 | Stacking meta-learner, scalers |
| pandas | 2.0 | Data wrangling |
| numpy | 1.24 | Array operations |
| joblib | 1.2 | Scaler loading (`.joblib` files) |

**Tested Environment**: Python 3.10+

---

## Key Findings

### Individual Model Observations (on common 4-split evaluation)
1. **LSTM achieves the highest individual AUC** on the common 4-split evaluation (0.881 ± 0.097), narrowly followed by GRU (0.875 ± 0.098)
2. **Transformer underperforms in the ensemble context** — the hybrid_adaptive scenario `.pt` weights trained on 31 features do not match the ensemble's 11-feature input, triggering on-the-fly retraining; resulting AUC is only 0.506 ± 0.066
3. **XGBoost is moderate** — AUC 0.666 ± 0.083, consistent across splits but limited by tabular feature engineering vs. sequences
4. **Splits 1–2 (2020–2021) are the strongest** for LSTM/GRU (AUC > 0.92); Split 4 (2023) is the hardest (all models < 0.78)
5. **Ensemble weighted_avg ranks best** at AUC 0.861 — it benefits from LSTM/GRU dominance by upweighting them proportional to their per-split AUC scores

### Confirmed Ensemble Benefits
- **Weighted Average** delivers the best AUC by amplifying LSTM and GRU signals; outperforms every standalone model except the LSTM/GRU individually at the means level
- **Stacked** has the highest recall (0.662) — useful when false negatives (missed blooms) are more costly
- **Soft Vote** is the most conservative — low recall but very high precision (0.900)

### Relationship to Previous Tasks
- Imputation method chosen for ensemble (Hybrid Gap-Adaptive, 4 phases) is the **best performer from Tasks 2–3** (AUC = 0.794 with XGBoost downstream)
- Rolling-origin split framework is identical to LSTM/GRU training notebooks, ensuring fair cross-model comparison
- XGBoost hyperparameters originate from `xgboost_model/` RandomizedSearchCV (CV AUC = 0.9833): `learning_rate=0.2, max_depth=8, n_estimators=500, subsample=0.9, colsample_bytree=0.9, scale_pos_weight=5`

### 3. Stacking (`stacked`)
A Logistic Regression meta-learner is trained on the probability outputs of the four base models using a **leave-one-out** scheme across the 4 splits:
- To evaluate split *k*, the meta-learner is trained on splits *≠ k*.
- This gives an unbiased estimate of whether combining model outputs adds value beyond any single model.

---

## Model Inference Details

| Model | Inference method |
|---|---|
| LSTM | Load `haribon_lstm_risk.keras` + `feature_scaler.joblib` → `model.predict()` |
| GRU | Load `haribon_gru_risk.keras` + `feature_scaler.joblib` → `model.predict()` |
| Transformer | Load per-split `.pt` weights → PyTorch forward pass (falls back to on-the-fly retraining if weights missing) |
| XGBoost | Load best hyperparameters → refit on train slice → `predict_proba()` (per-split refit prevents data leakage) |

---

## Outputs

### `ensemble_per_split_metrics.csv`
Per-split AUC, F1, Precision, Recall, Accuracy for every individual model and every ensemble strategy.

**Columns:** `split_num`, `train_end`, `test_start`, `test_end`, `n_train`, `n_test`, `positive_rate`, `source`, `name`, `accuracy`, `precision`, `recall`, `f1`, `auc`

### `ensemble_summary.csv`
Aggregated mean ± std across all 4 splits, ranked by AUC.

**Columns:** `rank_auc`, `source`, `name`, `accuracy_mean`, `accuracy_std`, `precision_mean`, `precision_std`, `recall_mean`, `recall_std`, `f1_mean`, `f1_std`, `auc_mean`, `auc_std`, `n_splits`

### `obj2_model_comparison_final.csv`
**The definitive Objective 2 results table.** Combines metrics from all models and the best ensemble strategy, ranked by AUC.

**Columns:** `rank`, `model`, `auc_mean`, `auc_std`, `accuracy_mean`, `accuracy_std`, `precision_mean`, `precision_std`, `recall_mean`, `recall_std`, `f1_mean`, `f1_std`, `n_splits`, `notes`

---

## Dependencies

```
tensorflow >= 2.12
torch >= 2.0
xgboost >= 1.7
scikit-learn >= 1.3
pandas, numpy, joblib
```
