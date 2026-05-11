# Objective 2, Task 5 — Ensemble Model for HAB Detection (Updated / Fixed Run)
## 1. Overview
Objective 2, Task 5 finalizes the HARIBON HAB detection benchmark by combining the four independently trained base models into a single **ensemble evaluation pipeline**:
- **LSTM** (Keras)
- **GRU** (Keras)
- **Transformer Encoder** (PyTorch)
- **XGBoost** (tabular refit-per-split)

The ensemble evaluates three combination strategies on a shared rolling-origin split framework:
- **soft vote** (`soft_vote`)
- **weighted average** (`weighted_avg`)
- **stacked meta-learning** (`stacked`, leave-one-out Logistic Regression)

This updated report reflects the **fixed ensemble pipeline** and the latest **6-split** results produced by:

```bash
cd ensemble_model
python run_ensemble.py --transformer-scenario hybrid_adaptive
```

## 2. Dataset and Feature Configuration
### 2.1 Source Dataset
- **File**: `final_compiled_dataset/Combined_Labeled.csv`
- **Coverage**: daily observations (2016–2026)
- **Target**: `red_tide_label` → binarized at threshold \( \ge 0.5 \) → `red_tide_binary`
- **Locations**: coastal monitoring sites in Capiz Province, Philippines (location-identified rows)

### 2.2 Features (11)
All base models are evaluated on the same 11-variable feature set used throughout the Objective 2 pipeline:
- `CHL`, `NDVI_daily`, `mlotst`, `precip_mm_day`,
- `so`, `thetao`, `uo`, `vo`,
- `wind_speed_ms`, `wind_u_ms`, `wind_v_ms`

### 2.3 Imputation Pipeline (Hybrid Gap‑Adaptive)
This run uses **`hybrid_adaptive`** imputation (Objective 1’s best-performing method), applied before split generation:
- Phase 1: linear interpolation (≤14-day gaps per location)
- Phase 2: climatological mean (Location × Month)
- Phase 3: location mean fallback
- Phase 4: global mean fallback (emergency)

## 3. Rolling-Origin Split Framework (6 Splits)
The ensemble uses **6 aligned yearly rolling-origin splits** (shared across LSTM/GRU/Transformer/XGBoost within the ensemble runner):
- Split 1: train ≤ 2019-12-31 | test = 2020
- Split 2: train ≤ 2020-12-31 | test = 2021
- Split 3: train ≤ 2021-12-31 | test = 2022
- Split 4: train ≤ 2022-12-31 | test = 2023
- Split 5: train ≤ 2023-12-31 | test = 2024
- Split 6: train ≤ 2024-12-31 | test = 2025–2026

## 4. Ensemble Pipeline (Implementation)
The ensemble runner is organized into four phases:
- **Phase 1 — Data** (`ensemble_model/code/ensemble_data.py`): load dataset, apply imputation, construct per-split train/test arrays.
- **Phase 2 — Inference** (`ensemble_model/code/ensemble_inference.py`): produce per-split probability vectors for each base model.
- **Phase 3 — Strategies** (`ensemble_model/code/ensemble_strategies.py`): combine probabilities using soft vote / weighted average / stacking.
- **Phase 4 — Evaluation** (`ensemble_model/code/ensemble_evaluate.py`): compute metrics, write CSV outputs, and compile Obj 2 comparison.

Outputs are written to `ensemble_model/results/`:
- `ensemble_per_split_metrics.csv` (per split × model/strategy)
- `ensemble_summary.csv` (mean ± std across splits)
- `obj2_model_comparison_final.csv` (final Objective 2 ranking table)

## 5. Fixes Included in the Updated Ensemble Model
This updated runner includes three practical fixes that affect reproducibility and correctness on the current environment:

### 5.1 Transformer weight loading works without `transformer_model/code/`
Some workspaces contain only the Transformer training notebook (`transformer_model/transformer_training.ipynb`) and saved `.pt` weights, without Python modules under `transformer_model/code/`.

The ensemble now remains able to load and run the Transformer by reconstructing the **same architecture and `TrainConfig` defaults** used in the notebook when the module import is unavailable. This enables direct inference from the existing per-split `.pt` files.

### 5.2 Keras 3 deserialization compatibility (LSTM)
The LSTM loader now applies the same Keras deserialization shim as the GRU loader (dropping `quantization_config` in Dense config) to prevent load failures under Keras 3.

### 5.3 Windows console encoding crash removed
The final “best model” print line now uses ASCII-only output to avoid `UnicodeEncodeError` on Windows cp1252 consoles.

## 6. Updated Results (6 Splits, `hybrid_adaptive`)
The summary below comes directly from `ensemble_model/results/ensemble_summary.csv` (mean ± std over 6 splits):

- **Best ensemble strategy (by AUC)**: **Ensemble (stacked)**
  - AUC = **0.9134 ± 0.0936**
  - F1 = **0.6593 ± 0.2066**
  - Recall = **0.8281 ± 0.2472**
  - n_splits = **6**

Other key rows:
- **LSTM**: AUC = **0.9042 ± 0.1102** (n_splits = 6)
- **GRU**: AUC = **0.9115 ± 0.0947** (n_splits = 6)
- **Weighted average**: AUC = **0.8913 ± 0.1009** (n_splits = 6)
- **Soft vote**: AUC = **0.8778 ± 0.1058** (n_splits = 6)
- **XGBoost**: AUC = **0.7195 ± 0.1074** (n_splits = 6)
- **Transformer**: AUC = **0.6265 ± 0.1975** (n_splits = 6)

## 7. Objective 2 Final Model Comparison (Updated)
The updated Objective 2 ranking table is written to:
- `ensemble_model/results/obj2_model_comparison_final.csv`

Top row (best overall):
- **Ensemble (stacked)** — AUC = **0.9134**, n_splits = **6**

## 8. Limitations and Reporting Notes
- **Base-model comparability**: `obj2_model_comparison_final.csv` may include base-model rows sourced from prior task result CSVs (e.g., Task 4 XGBoost summary, Transformer summary) which may use different aggregation conventions. The ensemble summary CSV is the most direct “apples-to-apples” comparison across the same 6 splits.
- **Transformer scenario**: For thesis alignment and pipeline consistency, this final ensemble run uses `--transformer-scenario hybrid_adaptive`.
- **Runtime**: XGBoost is refit per split to avoid leakage; this increases runtime but preserves evaluation integrity.

## 9. Reproducibility Checklist
- Confirm base-model artifacts exist:
  - `lstm/saved_model/haribon_lstm_risk.keras`
  - `gru/saved_model/haribon_gru_risk.keras`
  - Transformer weights for the selected scenario/splits:
    - `transformer_model/saved_model/transformer_hybrid_adaptive_split1.pt` … `split6.pt`
  - `xgboost_model/results/best_parameters.txt` (used to refit per split)
- Run:

```bash
python ensemble_model/run_ensemble.py --transformer-scenario hybrid_adaptive
```

