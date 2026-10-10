# Model Evaluation Against Baselines

Scores every model against simple predictors that use no environmental data, on the 6 rolling-origin splits. Every model in a table is scored on the same rows.

## Metrics

| Metric | Question it answers |
|---|---|
| `pooled_auc` | Ranks banned vs clear days across all sites together. This rewards telling sites apart. |
| `per_site_auc` | Ranks banned vs clear days within each site, averaged over sites that have both in the test year. |
| `onset_auc_7d` / `onset_auc_14d` | On days not under a ban: will a ban start within 7 or 14 days? This is the early-warning question. |
| `accuracy`, `precision`, `recall`, `f1` | Next-day ban prediction at a 0.5 probability cutoff, pooled across sites. |

## Baselines

| Baseline | Prediction |
|---|---|
| `persistence` | Yesterday's label |
| `site_prior` | The site's ban rate over the last 365 days of training |
| `climatology` | The site's ban rate for that calendar month during training |

## Scripts

| Script | What it does |
|---|---|
| `baselines.py` | Scores the saved models as they are (`--no-models` for baselines only) |
| `retrain_leakfree.py` | Retrains LSTM, GRU, Transformer and XGBoost without look-ahead, and scores them alongside `env_model` |
| `train_dl_anomaly.py` | Trains LSTM, GRU and Transformer on the `env_model` features instead of raw daily values (`--all-drivers` for all 11 environmental parameters) |
| `plot_model_comparison.py` | Draws the all-site and per-site AUC chart (`results/figures/model_comparison_auc.png`) from the saved summaries |

`retrain_leakfree.py` keeps the original architectures, lookback, loss and features, and changes only what leaked or was mis-validated:

- **Imputation:** forward-fill for up to 14 days, then training-period climatology. The original filled gaps from both directions and from all years.
- **Early stopping (LSTM/GRU):** the epoch count is chosen on the last 365 days of training across all sites, then the model is refit on the full training period. The original stopped on the tail of the concatenated array, which is a single site, and never refit.
- **Early stopping (Transformer):** its trainer holds out the last 20% of rows. Rows are sorted by date, so this is the most recent period across all sites.
- **Windows:** 30-day windows are built over calendar days. The original built them over consecutive labeled rows.
- **XGBoost tuning:** year-blocked folds. The original used non-temporal 3-fold CV.

Models are written to `saved_model/leakfree/`, which is not tracked in git. The production artifacts are not touched.

## Results: leak-free retraining (`results/leakfree_summary.csv`)

Data: `final_compiled_dataset/Combined_Labeled_2_0.csv` (9 sites, month/day swap corrected, labelled through 2026-10-01).

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Persistence | 0.996 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.755 | 0.500 | 0.608 | 0.609 |
| Site rate by month | 0.729 | **0.689** | 0.653 | 0.652 |
| LSTM | 0.654 | 0.544 | 0.672 | 0.649 |
| GRU | 0.675 | 0.438 | 0.654 | **0.662** |
| Transformer | 0.547 | 0.420 | 0.561 | 0.568 |
| XGBoost | 0.703 | 0.534 | 0.621 | 0.633 |
| Env model (`env_model/`) | **0.803** | 0.667 | 0.648 | 0.646 |

**All-sites AUC by split:**

| Split (test year) | LSTM | GRU | Transformer | XGBoost | Env model |
|---|---|---|---|---|---|
| 1 (2020) | 0.66 | 0.61 | 0.52 | 0.77 | 0.93 |
| 2 (2021) | 0.42 | 0.44 | 0.22 | 0.56 | 0.70 |
| 3 (2022) | 0.73 | 0.74 | 0.57 | 0.62 | 0.82 |
| 4 (2023) | 0.54 | 0.54 | 0.36 | 0.57 | 0.84 |
| 5 (2024) | 0.72 | 0.81 | 0.72 | 0.80 | 0.57 |
| 6 (2025–26) | 0.85 | 0.91 | 0.90 | 0.91 | 0.96 |

## Results: deep models on the environment-driven features (`results/dl_anomaly_summary.csv`)

`train_dl_anomaly.py` gives LSTM, GRU and Transformer 30-day sequences of the 11 `env_model` features (site-relative sea temperature and rainfall anomalies, season, ONI, earlier-year ban history) instead of raw daily values. Training uses the same testing-delay sample weights and no class reweighting. The networks are small (16 recurrent units; one 2-head attention layer), and each model is the average of 3 random starts.

| Model | All sites | Within site | Onset 7d | Onset 14d | Worst split (all sites) |
|---|---|---|---|---|---|
| Site rate by month | 0.729 | **0.689** | 0.653 | 0.652 | 0.53 |
| LSTM | 0.767 | 0.662 | 0.651 | **0.652** | 0.56 |
| GRU | 0.790 | 0.654 | 0.619 | 0.613 | **0.59** |
| Transformer | 0.776 | 0.682 | 0.644 | 0.642 | 0.47 |
| Mean of the three deep models | 0.781 | 0.666 | 0.637 | 0.637 | 0.54 |
| Deep mean + logistic regression | 0.797 | 0.669 | 0.646 | 0.644 | 0.56 |
| Logistic regression (`env_model`) | **0.803** | 0.667 | 0.648 | 0.646 | 0.57 |

**Change from the raw-value deep models (previous table):**

| Model | All sites | Within site |
|---|---|---|
| LSTM | 0.654 → 0.767 | 0.544 → 0.662 |
| GRU | 0.675 → 0.790 | 0.438 → 0.654 |
| Transformer | 0.547 → 0.776 | 0.420 → 0.682 |

**Deployed model.** The daily forecast uses the ensemble in the "Deep mean + logistic regression" row: each deep model's 3 seeds are averaged, the three deep models are averaged, and that is averaged with the logistic regression. `env_model/export_deployment.py` trains the final versions on all data; if the deep models cannot run, the forecast falls back to the logistic regression alone.

**All metrics** (raw-input rows from `results/leakfree_summary.csv`, the rest from `results/dl_anomaly_summary.csv`; classification metrics at a 0.5 cutoff):

| Model | All-site AUC | Within-site AUC | Onset 14d AUC | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| Site rate by month | 0.729 | 0.689 | 0.652 | 0.753 | 0.551 | 0.152 | 0.234 |
| XGBoost (raw inputs) | 0.703 | 0.534 | 0.633 | 0.704 | 0.382 | 0.453 | 0.398 |
| LSTM (raw inputs) | 0.654 | 0.544 | 0.649 | 0.752 | 0.343 | 0.021 | 0.040 |
| GRU (raw inputs) | 0.675 | 0.438 | 0.662 | 0.751 | 0.346 | 0.008 | 0.015 |
| Transformer (raw inputs) | 0.547 | 0.420 | 0.568 | 0.462 | 0.191 | 0.667 | 0.294 |
| LSTM (new features) | 0.767 | 0.662 | 0.652 | 0.773 | 0.642 | 0.320 | 0.396 |
| GRU (new features) | 0.790 | 0.654 | 0.613 | 0.779 | 0.647 | 0.446 | 0.498 |
| Transformer (new features) | 0.776 | 0.682 | 0.642 | 0.775 | 0.476 | 0.331 | 0.374 |
| Logistic regression | 0.803 | 0.667 | 0.646 | 0.795 | 0.683 | 0.441 | 0.502 |
| **Ensemble (deployed)** | 0.797 | 0.669 | 0.644 | **0.801** | **0.692** | 0.448 | **0.514** |

Recall at a 0.5 cutoff is modest for the calibrated models because a calibrated probability rarely reaches 0.5 except at sites already under a ban; the forecast's risk levels use lower cutoffs (0.32 / 0.45 / 0.60). Day-level predictions for the new-feature models are in `results/dl_anomaly_predictions.csv`, so other cutoffs can be scored without retraining.

The change of inputs, not of architecture, accounts for the improvement: within-site AUC rises from near chance to about the level of the monthly baseline. With the same inputs, the deep models and the logistic regression perform about the same; the Transformer has the best within-site AUC of the trained models (0.682) but the weakest single split (0.47 in 2024).

## Results: other environmental parameters

`env_model/compare_drivers.py` and `train_dl_anomaly.py --all-drivers` give chlorophyll-a, salinity, mixed layer depth, NDVI, wind (speed, u, v) and currents (u, v) the same treatment as sea temperature and rainfall: site-relative anomalies with 30/60/90-day rolling means. Each set is scored on the same splits and rows.

| Model | Inputs | All-site AUC | Per-site AUC | Precision | F1 |
|---|---|---|---|---|---|
| Logistic regression | sea temperature + rainfall | **0.803** | **0.667** | **0.682** | 0.501 |
| Logistic regression | all except NDVI | 0.770 | 0.599 | 0.631 | 0.526 |
| Logistic regression | all 11 | 0.746 | 0.557 | 0.593 | 0.488 |
| LSTM | all 11 | 0.736 | 0.526 | 0.516 | 0.397 |
| GRU | all 11 | 0.749 | 0.559 | 0.535 | 0.432 |
| Transformer | all 11 | 0.756 | 0.497 | 0.451 | 0.342 |
| Ensemble | all 11 | 0.757 | 0.548 | 0.594 | 0.471 |

Adding any single parameter to the logistic regression leaves per-site AUC at 0.615–0.672; the two small gains (east–west wind and current) come only from 2020, when 3 sites are scored. Within sites, sea temperature anomalies point the same way at 8 of 9 sites, while salinity, mixed layer depth and NDVI change direction between sites, so a pooled model can only use them to tell sites apart. Chlorophyll-a points the same way at 7 of 9 sites but is weak (within-site AUC 0.57).

## Findings

1. **The original models' published scores came from corrupted data.** In `Combined_Labeled.csv`, about 36% of rows have month and day swapped (see `final_compiled_dataset/fix_date_swap.py`), and their scores also benefited from look-ahead imputation. None of the earlier numbers should be reported.
2. **On raw inputs, the sequence models do not learn within-site patterns.** Their within-site AUC is 0.42–0.54, close to chance and well below the monthly baseline (0.69).
3. **The env model is best across sites** (0.803) and better within sites than the sequence models and XGBoost. It does not beat the monthly baseline within sites (0.667 vs 0.689). Its worst split is 0.57, about the same as XGBoost (0.56) and better than the raw-input deep models (0.22–0.44).
4. **On raw inputs, the deep models are unstable.** Across three retraining runs the raw-input Transformer's mean all-site AUC was 0.575, 0.661 and 0.547, and its 2021 AUC ranged from 0.22 to 0.78; the last two runs used identical data. On the new features, a rerun reproduced every deep-model AUC exactly, and the env model's results did not change.
5. **The deep models were held back by their inputs, not their architecture.** Trained on site-relative anomalies instead of raw values, LSTM, GRU and Transformer reach 0.77–0.79 all-site and 0.65–0.68 within-site AUC, close to the logistic regression on the same features (0.803 / 0.667).
6. **No model clearly beats the monthly baseline at predicting when a ban starts.** Onset 14d AUC ranges from 0.57 to 0.66 against 0.652 for the baseline; with 51 ban starts the onset results are too noisy to separate the models.
7. **The deployed ensemble has the best classification metrics** at a 0.5 cutoff (accuracy 0.801, precision 0.692, F1 0.514).
8. **More environmental parameters make every model worse.** With all 11 parameters, per-site AUC falls to 0.50–0.56 for every model (Ensemble 0.669 → 0.548), back near the raw-input models. Sea temperature and rainfall anomalies are the only parameters kept.

## Usage

```bash
cd evaluation
python baselines.py
python retrain_leakfree.py          # ~2 h on CPU
python train_dl_anomaly.py          # ~1.5 h on CPU
python train_dl_anomaly.py --all-drivers
python plot_model_comparison.py
```
