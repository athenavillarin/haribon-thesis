# Transformer Model (Objective 2, Task 4)

This folder contains the **Transformer Encoder** HAB classifier for Objective 2, Task 4.

## What this runs

The notebook [`transformer_training.ipynb`](transformer_training.ipynb) evaluates two Transformer scenarios with the same Pre-LN architecture and rolling-origin validation scheme:

1. **`hybrid_adaptive`**: uses the Hybrid Gap-Type Adaptive imputation from Objective 1
2. **`native_masking`**: keeps missingness indicators and trains without imputation

The current notebook training loop uses:

* **Binary Focal Loss** with `alpha=0.25` and `gamma=2.0`
* **Inverse-frequency class weights** computed per split
* **F1-optimized validation threshold** clipped to `[0.1, 0.5]`
* **6 year-based rolling splits**
* **AdamW** optimizer and **early stopping** with `patience=8`

## Usage

Open the notebook and run the cells in order:

```bash
cd transformer_model
jupyter notebook transformer_training.ipynb
```

To refresh the evaluation tables and plots, rerun the 6-split training cell, then run the per-split and aggregate reporting cells. Skip the final retraining cell if you only want cross-validation results.

## Outputs

Saved to `transformer_model/results/`:

* `transformer_per_split_metrics.csv` - split-level metrics for each scenario
* `transformer_summary.csv` - mean/std summary across splits
* `transformer_hybrid_vs_native.csv` - direct deltas (`hybrid_adaptive - native_masking`)

If you run the final retraining cell, the notebook also saves scenario-specific `.pt` model checkpoints to `transformer_model/saved_model/`.

## Dependency

PyTorch is required:

```bash
pip install torch
```

## Label handling

* Uses `red_tide_label` as target.
* Converts to binary class using `label_threshold` (default `0.5`).

## Current results

In the current run, hybrid_adaptive ranks higher on AUC, Accuracy, Recall, and F1. native_masking leads marginally on Precision.

The notebook [`transformer_training.ipynb`](transformer_training.ipynb) is the source of truth for the detailed split-level metrics and runtime tracking.
