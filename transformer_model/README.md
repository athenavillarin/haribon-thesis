# Transformer Model (Objective 2, Task 4)

This folder is for **Objective 2 - Task 4: transformer model**.

## What this runs

A **Transformer Encoder**-based HAB classifier under two approaches:

1. **`hybrid_adaptive`**: uses the best imputation strategy from Objective 1 (Hybrid: Gap-Type Adaptive)
2. **`native_masking`**: no imputation; model is trained with masked values and explicit missingness indicators

Both scenarios are evaluated with generated **rolling-origin splits** from the final labeled timeline.

## Usage

Use the Jupyter notebook for training with detailed timing measurements:

```bash
cd transformer_model
jupyter notebook transformer_training.ipynb
```

The notebook includes all functionality with runtime tracking for each split.

## Outputs

Saved to `transformer_model/results/`:

- `transformer_per_split_metrics.csv` – split-level metrics for each scenario
- `transformer_summary.csv` – mean/std summary across splits
- `transformer_hybrid_vs_native.csv` – direct deltas (`hybrid_adaptive - native_masking`)

## Dependency

- PyTorch is required:

```bash
pip install torch
```

## Label handling

- Uses `red_tide_label` as target.
- Converts to binary class using `label_threshold` (default `0.5`).

## Key findings (current run)

Using:

```bash
python run_transformer.py --num-splits 6 --test-window-days 365 --min-train-days 365
```

Results will be saved to `transformer_model/results/` with metrics: Accuracy, Precision, Recall, F1-Score, AUC-ROC.

The Jupyter notebook `transformer_training.ipynb` provides detailed training with runtime measurements for each split.
