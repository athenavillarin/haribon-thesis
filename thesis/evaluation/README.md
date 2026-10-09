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
- **Early stopping:** the last 365 days of training across all sites. The original used the tail of the concatenated array, which is a single site.
- **XGBoost tuning:** year-blocked folds. The original used non-temporal 3-fold CV.

Models are written to `saved_model/leakfree/`, which is not tracked in git. The production artifacts are not touched.

## Results: leak-free retraining (`results/leakfree_summary.csv`)

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Persistence | 0.995 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.788 | 0.500 | 0.636 | 0.630 |
| Site rate by month | 0.751 | 0.667 | 0.691 | 0.669 |
| LSTM | 0.658 | 0.493 | 0.671 | 0.670 |
| GRU | 0.663 | 0.527 | 0.695 | 0.682 |
| Transformer | 0.728 | 0.539 | 0.681 | 0.687 |
| XGBoost | 0.744 | 0.495 | 0.669 | 0.661 |
| Env model (`env_model/`) | **0.831** | **0.642** | 0.621 | 0.605 |

**All-sites AUC by split:**

| Split (test year) | LSTM | GRU | Transformer | XGBoost | Env model |
|---|---|---|---|---|---|
| 1 (2020) | 0.98 | 0.96 | 0.98 | 0.87 | 0.88 |
| 2 (2021) | 0.37 | 0.34 | 0.46 | 0.61 | 0.77 |
| 3 (2022) | 0.16 | 0.26 | 0.62 | 0.59 | 0.81 |
| 4 (2023) | 0.47 | 0.49 | 0.48 | 0.56 | 0.89 |
| 5 (2024) | 0.99 | 0.98 | 0.98 | 0.86 | 0.65 |
| 6 (2025–26) | 0.98 | 0.94 | 0.84 | 0.97 | 1.00 |

## Findings

1. **The sequence models learn which sites are usually banned.** They score about 0.98 in years whose ban pattern repeats the past (2020, 2024, 2025–26). They fall to 0.16–0.49 in 2021–23, when the Capiz sites had their first bans. Their within-site AUC is close to chance (0.49–0.54).
2. **The saved models' scores were inflated by look-ahead imputation.** Retrained without it, the Transformer drops from 0.846 to 0.728 (all sites) and from 0.774 to 0.687 (onset 14d).
3. **The env model is the most reliable.** It has the best all-sites and within-site AUC, and its worst split is 0.65, compared with 0.16–0.56 for the others.
4. **No model clearly beats the monthly baseline at predicting when a ban starts.** Every model lands between 0.60 and 0.69, against 0.669 for the baseline. With about 130 onsets in the data, the onset results are too noisy to separate the models.

## Usage

```bash
cd evaluation
python baselines.py
python retrain_leakfree.py          # ~1.5 h on CPU
```
