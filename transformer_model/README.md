# Transformer Model (Objective 2, Task 4)

This folder is for **Objective 2 - Task 4: transformer model**.

## What this runs

A Transformer-based HAB classifier under two approaches:

1. **`hybrid_adaptive`**: uses the best imputation strategy from Objective 1 (Hybrid: Gap-Type Adaptive)
2. **`native_masking`**: no imputation; model is trained with masked values and explicit missingness indicators

Both scenarios are evaluated with generated **rolling-origin splits** from the final labeled timeline.

## Usage

From repo root:

```bash
cd transformer_model
python run_transformer.py
```

Run only one scenario:

```bash
python run_transformer.py --scenarios hybrid_adaptive
```

Run with explicit dataset/split configuration:

```bash
python run_transformer.py --dataset-path ../final_compiled_dataset/Combined_Labeled.csv --num-splits 4 --test-window-days 90 --min-train-days 365
```

Adjust sequence and model size:

```bash
python run_transformer.py --history-days 45 --epochs 60 --d-model 96 --num-layers 3
```

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
python run_transformer.py --num-splits 4 --test-window-days 90 --min-train-days 365
```

Summary from `transformer_summary.csv`:

- **Best scenario by AUC:** `native_masking`
- **AUC mean:** `0.7758` (`native_masking`) vs `0.6634` (`hybrid_adaptive`)
- **F1 mean:** `0.2534` (`native_masking`) vs `0.2173` (`hybrid_adaptive`)
- **Accuracy mean:** `0.6967` (`native_masking`) vs `0.7139` (`hybrid_adaptive`)

Interpretation:

- For Transformer in this setup, **native masking outperformed hybrid-adaptive imputation** on discrimination metrics (AUC, F1).
- This supports the thesis insight that the best imputation strategy from Objective 1 does not always produce the best downstream model performance.

Notes:

- Some splits can report `AUC=nan` when test labels contain only one class (AUC is undefined in that case).
