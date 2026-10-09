# Environment-Driven HAB Model

Logistic regression on slow-moving environmental drivers plus each site's ban history.

Data: `final_compiled_dataset/Combined_Labeled_2_0.csv`. This is the 7 original sites with the month/day swap corrected (see `fix_date_swap.py`), plus Milagros (Masbate) and Cancabato Bay, labelled through 2026-10-01. It holds 51 ban starts in total.

## Why this model

`evaluation/baselines.py` showed that the original models mostly recognised sites:

- Their AUC within a single site was close to chance.
- A lookup of each site's monthly ban rate scored higher.
- The top SHAP features (`mlotst`, `NDVI_daily`, `so`, `thetao`) vary more between sites than within them, so they act as site fingerprints.

Changes made here:

- **Site-relative anomalies.** Sea temperature and rainfall are compared with each site's monthly climatology and scaled by that site's standard deviation.
- **30/60/90-day rolling means, season and ENSO.** ONI is lagged 3 months so it is available on the date it is used. These slow-moving drivers were the only ones with a consistent within-site signal; satellite chlorophyll showed none.
- **Site ban history from earlier years only.** Each row's history features come from years before its own.
- **Testing-delay-aware weights.** Shellfish testing takes about 2 weeks, so the 14 days before a ban starts and the last 14 days of a ban get weight 0.3. Days with a real bulletin get weight 3. Weights use training labels only.
- **No look-ahead in features.** Gaps are forward-filled for up to 14 days, then filled from training-period climatology. Every statistic uses training dates only.
- **A small linear model.** With 51 ban starts, larger models fit noise and site identity.

## Results (9 sites, 6 rolling-origin splits, mean; all models scored on the same rows)

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Yesterday's label (persistence) | 0.996 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.755 | 0.500 | 0.608 | 0.609 |
| Site rate by month (climatology) | 0.729 | **0.689** | 0.653 | 0.652 |
| History features only | 0.774 | 0.689 | 0.629 | 0.629 |
| Environment only | 0.654 | 0.664 | 0.611 | 0.603 |
| **History + environment** | **0.799** | 0.665 | 0.647 | 0.645 |
| LSTM (retrained leak-free) | 0.639 | 0.534 | 0.669 | 0.661 |
| GRU (retrained leak-free) | 0.688 | 0.425 | 0.681 | **0.691** |
| Transformer (retrained leak-free) | 0.575 | 0.544 | 0.570 | 0.552 |
| XGBoost (retrained leak-free) | 0.693 | 0.528 | 0.625 | 0.632 |

The onset columns score whether a ban starts within 7 or 14 days, counting only days that are not already under a ban. The other model types were retrained on the same data by `evaluation/retrain_leakfree.py`; see `evaluation/README.md`.

**Within-site AUC by split:**

| Split (test year) | Sites scored | Climatology | Environment only | History + environment |
|---|---|---|---|---|
| 1 (2020) | 3 | 0.967 | 0.979 | 0.951 |
| 2 (2021) | 4 | 0.457 | 0.558 | 0.560 |
| 3 (2022) | 7 | 0.660 | 0.801 | 0.776 |
| 4 (2023) | 7 | 0.771 | 0.801 | 0.806 |
| 5 (2024) | 3 | 0.518 | 0.363 | 0.349 |
| 6 (2025–26) | 2 | 0.758 | 0.489 | 0.546 |

The environmental features beat the monthly baseline in 2021–23, when the most sites have both banned and clear days. They fall below it in 2024–26.

**Leave-one-site-out (environment only):** the model trains on the other sites up to 2021 and is tested on the held-out site from 2022 on, so neither that site nor that period is seen in training.

| Site | Region | AUC |
|---|---|---|
| Roxas City | Capiz | 0.872 |
| Sapian Bay | Capiz | 0.857 |
| Pilar | Capiz | 0.838 |
| Gigantes Islands | Capiz | 0.818 |
| President Roxas | Capiz | 0.814 |
| Cancabato Bay | Leyte | 0.563 |
| Matarinao Bay | Samar | 0.557 |
| Milagros (Masbate) | Masbate | 0.441 |
| Dumanquillas Bay | Zamboanga | n/a (banned every day after 2021) |

**Strongest drivers (standardized coefficients, final split):**

- site's ban rate over the previous year: +1.00
- season (`doy_cos` +0.71, `doy_sin` −0.56)
- 90-day sea temperature anomaly: +0.28
- 60-day rainfall anomaly: +0.17

## Limitations

- **The environmental signal does not transfer between regions.** Held-out Capiz sites score 0.81–0.87, but Leyte, Samar and Masbate score 0.44–0.56. The Capiz scores may also be helped by those sites going into bans at the same time. More sites per region, or a model per region, are needed.
- **Within sites, the model does not beat the monthly baseline overall** (0.665 vs 0.689). It does beat it in 2021–23.
- **The signal is seasonal-scale.** It does not give a sharp warning just before a ban: onset AUC is 0.65, about the same as the monthly baseline.
- **Some splits rest on very few sites.** Within-site AUC in 2025–26 uses 2 sites, and 2020 and 2024 use 3.

## Usage

```bash
cd env_model
python train_env_model.py --loso
cd ../evaluation
python retrain_leakfree.py
```
