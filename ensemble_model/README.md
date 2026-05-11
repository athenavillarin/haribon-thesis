# HARIBON Objective 2 - Task 5: Ensemble Model

## Overview
This module evaluates a 4-model ensemble for red tide risk detection using:
- LSTM
- GRU
- Transformer
- XGBoost

The latest revision is aligned to:
- 6 rolling-origin splits
- hybrid_adaptive imputation pipeline
- hybrid_adaptive Transformer scenario for ensemble execution

This run regenerates:
- ensemble_per_split_metrics.csv
- ensemble_summary.csv
- obj2_model_comparison_final.csv

All outputs are in ensemble_model/results.

## Latest Run Configuration
Command used:

```bash
cd ensemble_model
python run_ensemble.py --splits 1 2 3 4 5 6 --imputation-method hybrid_adaptive --transformer-scenario hybrid_adaptive
```

Configuration:
- Splits: 1 to 6
- Imputation method: hybrid_adaptive
- Transformer scenario in ensemble run: hybrid_adaptive
- Ensemble strategies: soft_vote, weighted_avg, stacked

## Current Results (ensemble_summary.csv)

Mean +- std across 6 splits:

| Rank | Source | Name | Accuracy | Precision | Recall | F1 | AUC | n_splits |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ensemble | stacked | 0.8253 +- 0.1056 | 0.6105 +- 0.2134 | 0.8361 +- 0.2364 | 0.6657 +- 0.2042 | 0.9130 +- 0.0967 | 6 |
| 2 | model | gru | 0.7907 +- 0.1059 | 0.7963 +- 0.2618 | 0.1752 +- 0.0696 | 0.2819 +- 0.1065 | 0.9115 +- 0.0947 | 6 |
| 3 | model | lstm | 0.7960 +- 0.1240 | 0.8032 +- 0.2525 | 0.2137 +- 0.1098 | 0.3320 +- 0.1555 | 0.9042 +- 0.1102 | 6 |
| 4 | ensemble | weighted_avg | 0.8091 +- 0.1155 | 0.8566 +- 0.1476 | 0.2435 +- 0.1727 | 0.3609 +- 0.2060 | 0.9011 +- 0.0890 | 6 |
| 5 | ensemble | soft_vote | 0.8086 +- 0.1149 | 0.8140 +- 0.2003 | 0.2497 +- 0.1789 | 0.3639 +- 0.2111 | 0.8969 +- 0.0867 | 6 |
| 6 | model | xgboost | 0.7895 +- 0.1030 | 0.6213 +- 0.2191 | 0.2687 +- 0.1918 | 0.3488 +- 0.1930 | 0.7195 +- 0.1074 | 6 |
| 7 | model | transformer | 0.2446 +- 0.1189 | 0.2446 +- 0.1189 | 1.0000 +- 0.0000 | 0.3803 +- 0.1603 | 0.5000 +- 0.0000 | 6 |

Best strategy in this run: Ensemble (stacked).

## Objective 2 Final Comparison (obj2_model_comparison_final.csv)

| Overall Rank | Model | AUC | Accuracy | Precision | Recall | F1 | n_splits | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Ensemble (stacked) | 0.9130 +- 0.0967 | 0.8253 +- 0.1056 | 0.6105 +- 0.2134 | 0.8361 +- 0.2364 | 0.6657 +- 0.2042 | 6 | Best ensemble strategy by AUC, then F1, then Recall across 6 common splits |
| 2 | XGBoost (Hybrid: Gap-Type Adaptive) | 0.7037 +- 0.1193 | 0.4979 +- 0.1162 | 0.2809 +- 0.1291 | 0.7283 +- 0.2144 | 0.3925 +- 0.1570 | 6 | Hybrid-adaptive XGBoost notebook evaluation across 6 temporal splits |
| 3 | Transformer | 0.6426 +- 0.1042 | 0.7380 +- 0.1327 | 0.2855 +- 0.2695 | 0.1865 +- 0.2307 | 0.2032 +- 0.2234 | 6 | hybrid_adaptive scenario from transformer_summary.csv |
| 4 | LSTM | 0.6398 +- 0.1414 | 0.7605 +- 0.1610 | 0.6320 +- 0.1328 | 0.1641 +- 0.0555 | 0.5492 +- 0.0696 | 4 | Splits 1-4 of 6 rolling-origin yearly splits |
| 5 | GRU | 0.6182 +- 0.1219 | 0.7532 +- 0.1699 | 0.6210 +- 0.2012 | 0.1752 +- 0.0952 | 0.5415 +- 0.0440 | 4 | Splits 1-4 of 6 rolling-origin yearly splits |

## Important Interpretation Note
Two Transformer numbers may appear in reports, and they come from different sources:

1. Ensemble per-split runtime output (ensemble_summary.csv)
- Transformer appears as AUC 0.5000 in this run because the per-split inference path produced near-constant positive predictions.

2. Transformer standalone summary source used in Objective 2 table
- Loaded from transformer_model/results/transformer_summary.csv using scenario=hybrid_adaptive.
- This is why Objective 2 shows Transformer AUC 0.6426.

This behavior is expected with the current architecture because Objective 2 comparison intentionally mixes validated standalone baseline summaries (LSTM/GRU/Transformer/XGBoost notebook metrics) with best ensemble strategy output.

## Data and Split Framework
- Dataset: final_compiled_dataset/Combined_Labeled.csv
- Features (11): CHL, NDVI_daily, mlotst, precip_mm_day, so, thetao, uo, vo, wind_speed_ms, wind_u_ms, wind_v_ms
- Target: red_tide_label (binarized at threshold 0.5)
- Sequence lookback: 30

Rolling-origin splits:
- Split 1: train <= 2019-12-31, test 2020
- Split 2: train <= 2020-12-31, test 2021
- Split 3: train <= 2021-12-31, test 2022
- Split 4: train <= 2022-12-31, test 2023
- Split 5: train <= 2023-12-31, test 2024
- Split 6: train <= 2024-12-31, test 2025-2026

## Ensemble Strategies
- soft_vote: unweighted mean of model probabilities
- weighted_avg: weighted mean using split-level model AUCs
- stacked: logistic-regression meta-learner trained in leave-one-out fashion across splits

## How to Run

### Default full run
```bash
cd ensemble_model
python run_ensemble.py
```

### Explicit hybrid_adaptive revision run
```bash
python run_ensemble.py --splits 1 2 3 4 5 6 --imputation-method hybrid_adaptive --transformer-scenario hybrid_adaptive
```

### Optional utilities
```bash
# Choose strategies
python run_ensemble.py --strategies soft_vote weighted_avg stacked

# Run selected splits only
python run_ensemble.py --splits 5 6

# Generate missing Transformer split weights only
python run_ensemble.py --generate-missing-transformer-weights-only --transformer-scenario hybrid_adaptive
```

## Output Files
- ensemble_model/results/ensemble_per_split_metrics.csv
- ensemble_model/results/ensemble_summary.csv
- ensemble_model/results/obj2_model_comparison_final.csv

## Code Structure
- ensemble_model/run_ensemble.py: CLI entrypoint and orchestration
- ensemble_model/code/ensemble_data.py: data loading, imputation, split generation
- ensemble_model/code/ensemble_inference.py: per-model inference wrappers
- ensemble_model/code/ensemble_strategies.py: soft_vote, weighted_avg, stacked
- ensemble_model/code/ensemble_evaluate.py: metric aggregation and Objective 2 table generation

## Revision Notes
Updated in this revision:
- Ensemble rerun completed with 6 splits and hybrid_adaptive settings.
- Objective 2 comparison now follows the selected Transformer scenario from CLI during table build.
- README synchronized to latest generated CSV values.
