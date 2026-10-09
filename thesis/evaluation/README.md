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

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Persistence | 0.995 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.788 | 0.500 | 0.636 | 0.630 |
| Site rate by month | 0.751 | 0.667 | 0.691 | 0.669 |
| LSTM | 0.698 | 0.447 | 0.639 | 0.624 |
| GRU | 0.733 | 0.508 | 0.693 | 0.673 |
| Transformer | 0.722 | 0.588 | 0.707 | 0.698 |
| XGBoost | 0.736 | 0.480 | 0.673 | 0.663 |
| Env model (`env_model/`) | **0.831** | **0.642** | 0.621 | 0.605 |

**All-sites AUC by split:**

| Split (test year) | LSTM | GRU | Transformer | XGBoost | Env model |
|---|---|---|---|---|---|
| 1 (2020) | 0.80 | 0.97 | 0.97 | 0.82 | 0.88 |
| 2 (2021) | 0.34 | 0.35 | 0.79 | 0.61 | 0.77 |
| 3 (2022) | 0.64 | 0.60 | 0.30 | 0.59 | 0.81 |
| 4 (2023) | 0.50 | 0.54 | 0.53 | 0.56 | 0.89 |
| 5 (2024) | 0.92 | 0.94 | 0.96 | 0.86 | 0.65 |
| 6 (2025–26) | 0.99 | 0.99 | 0.79 | 0.97 | 1.00 |

## Findings

1. **The sequence models learn which sites are usually banned.** They score 0.79–0.99 in years whose ban pattern repeats the past (2020, 2024, 2025–26). They fall to 0.30–0.64 in 2021–23, when the Capiz sites had their first bans. Their within-site AUC is close to chance (0.45–0.59).
2. **The saved models' scores do not hold up when retrained without look-ahead.** The Transformer drops from 0.846 to 0.722 (all sites) and from 0.774 to 0.698 (onset 14d). The retraining also changes validation and window construction, so not all of the drop can be attributed to imputation alone.
3. **The deep models are unstable.** Between two retraining runs that differed only in validation and refit details, the Transformer's 2021 AUC went from 0.46 to 0.79 and its 2022 AUC from 0.62 to 0.30.
4. **The env model is the most reliable.** It has the best all-sites and within-site AUC, its worst split is 0.65 (others: 0.30–0.56), and as a linear model it gives the same result on every run.
5. **No model clearly beats the monthly baseline at predicting when a ban starts.** Every model lands between 0.60 and 0.70, against 0.669 for the baseline. With about 130 onsets in the data, the onset results are too noisy to separate the models.

## Usage

```bash
cd evaluation
python baselines.py
python retrain_leakfree.py          # ~1.5 h on CPU
```
