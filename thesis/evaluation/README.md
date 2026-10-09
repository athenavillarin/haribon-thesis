# Model Evaluation Against Baselines

Scores every model against simple predictors that use no environmental data, on the 6 rolling-origin splits. Every model in a table is scored on the same rows.

## Metrics

| Metric | Question it answers |
|---|---|
| `pooled_auc` | Ranks banned vs clear days across all sites together. This rewards telling sites apart. |
| `per_site_auc` | Ranks banned vs clear days within each site, averaged over sites that have both in the test year. |
| `onset_auc_7d` / `onset_auc_14d` | On days not under a ban: will a ban start within 7 or 14 days? This is the early-warning question. |

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
| LSTM | 0.656 | 0.480 | 0.663 | 0.658 |
| GRU | 0.664 | 0.480 | **0.689** | **0.690** |
| Transformer | 0.661 | 0.414 | 0.654 | 0.658 |
| XGBoost | 0.703 | 0.534 | 0.621 | 0.633 |
| Env model (`env_model/`) | **0.799** | 0.665 | 0.647 | 0.645 |

**All-sites AUC by split:**

| Split (test year) | LSTM | GRU | Transformer | XGBoost | Env model |
|---|---|---|---|---|---|
| 1 (2020) | 0.59 | 0.60 | 0.53 | 0.77 | 0.92 |
| 2 (2021) | 0.42 | 0.39 | 0.78 | 0.56 | 0.69 |
| 3 (2022) | 0.72 | 0.73 | 0.70 | 0.62 | 0.82 |
| 4 (2023) | 0.54 | 0.53 | 0.52 | 0.57 | 0.84 |
| 5 (2024) | 0.81 | 0.84 | 0.74 | 0.80 | 0.57 |
| 6 (2025–26) | 0.86 | 0.90 | 0.70 | 0.91 | 0.96 |

## Findings

1. **The original models' published scores came from corrupted data.** In `Combined_Labeled.csv`, about 36% of rows have month and day swapped (see `final_compiled_dataset/fix_date_swap.py`), and their scores also benefited from look-ahead imputation. None of the earlier numbers should be reported.
2. **The sequence models do not learn within-site patterns.** Their within-site AUC is 0.41–0.48, below chance and well below the monthly baseline (0.69).
3. **The env model is best across sites** (0.799) and better within sites than the sequence models and XGBoost. It does not beat the monthly baseline within sites (0.665 vs 0.689). Its worst split is 0.57, about the same as XGBoost (0.56) and better than the others (0.39–0.52).
4. **The deep models are unstable.** Adding three weeks of data (labels through 2026-10-01 instead of 2026-09-07) moved the Transformer's 2021 AUC from 0.24 to 0.78 and its mean from 0.575 to 0.661. The env model's results did not change.
5. **No model clearly beats the monthly baseline at predicting when a ban starts.** GRU is highest at 0.690 against 0.652 for the baseline, but with 51 ban starts the onset results are too noisy to separate the models.

## Usage

```bash
cd evaluation
python baselines.py
python retrain_leakfree.py          # ~2 h on CPU
```
