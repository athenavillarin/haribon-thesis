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
- **Calibrated probabilities.** Ban and clear days are not reweighted to equal totals. Reweighting gave the same ranking but pushed every probability toward 0.5: clear Capiz days averaged 0.33 and 29% of them reached the forecast's Moderate cutoff (0.45). Unweighted, the mean predicted probability (0.23) matches the ban rate (0.25), clear Capiz days average 0.12, and 9% reach Moderate.

## Results (9 sites, 6 rolling-origin splits, mean; all models scored on the same rows)

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Yesterday's label (persistence) | 0.996 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.755 | 0.500 | 0.608 | 0.609 |
| Site rate by month (climatology) | 0.729 | **0.689** | 0.653 | 0.652 |
| History features only | 0.773 | 0.689 | 0.629 | 0.628 |
| Environment only | 0.658 | 0.669 | 0.605 | 0.599 |
| **History + environment** | **0.803** | 0.667 | 0.648 | 0.646 |
| LSTM (retrained leak-free) | 0.654 | 0.544 | 0.672 | 0.649 |
| GRU (retrained leak-free) | 0.675 | 0.438 | 0.654 | 0.662 |
| Transformer (retrained leak-free) | 0.547 | 0.420 | 0.561 | 0.568 |
| XGBoost (retrained leak-free) | 0.703 | 0.534 | 0.621 | 0.633 |
| LSTM on these features | 0.767 | 0.662 | 0.651 | 0.652 |
| GRU on these features | 0.790 | 0.654 | 0.619 | 0.613 |
| Transformer on these features | 0.776 | 0.682 | 0.644 | 0.642 |

The "retrained leak-free" rows use the original raw daily inputs. The "on these features" rows are the same model types trained on this model's features by `evaluation/train_dl_anomaly.py`; with the same inputs they perform about as well as this model. The onset columns score whether a ban starts within 7 or 14 days, counting only days that are not already under a ban. The other model types were retrained on the same data by `evaluation/retrain_leakfree.py`; see `evaluation/README.md`.

**Within-site AUC by split:**

| Split (test year) | Sites scored | Climatology | Environment only | History + environment |
|---|---|---|---|---|
| 1 (2020) | 3 | 0.967 | 0.969 | 0.952 |
| 2 (2021) | 4 | 0.457 | 0.573 | 0.565 |
| 3 (2022) | 7 | 0.660 | 0.800 | 0.792 |
| 4 (2023) | 7 | 0.771 | 0.805 | 0.814 |
| 5 (2024) | 3 | 0.518 | 0.371 | 0.346 |
| 6 (2025–26) | 2 | 0.762 | 0.499 | 0.531 |

The environmental features beat the monthly baseline in 2021–23, when the most sites have both banned and clear days. They fall below it in 2024–26.

**Leave-one-site-out (environment only):** the model trains on the other sites up to 2021 and is tested on the held-out site from 2022 on, so neither that site nor that period is seen in training.

| Site | Region | AUC |
|---|---|---|
| Roxas City | Capiz | 0.875 |
| Sapian Bay | Capiz | 0.868 |
| Pilar | Capiz | 0.849 |
| Gigantes Islands | Capiz | 0.836 |
| President Roxas | Capiz | 0.812 |
| Matarinao Bay | Samar | 0.567 |
| Cancabato Bay | Leyte | 0.559 |
| Milagros (Masbate) | Masbate | 0.456 |
| Dumanquillas Bay | Zamboanga | n/a (banned every day after 2021) |

**Other environmental parameters:** adding chlorophyll-a, salinity, mixed layer depth, NDVI, wind and currents lowers per-site AUC (all 11: 0.557; all except NDVI: 0.599; see `compare_drivers.py` and `evaluation/README.md`), so only sea temperature and rainfall are used.

**Strongest drivers (standardized coefficients, final split):**

- site's ban rate over the previous year: +1.01
- season (`doy_cos` +0.67, `doy_sin` −0.50)
- 90-day sea temperature anomaly: +0.22
- 60-day rainfall anomaly: +0.11

## Limitations

- **The environmental signal does not transfer between regions.** Held-out Capiz sites score 0.81–0.88, but Leyte, Samar and Masbate score 0.46–0.57. The Capiz scores may also be helped by those sites going into bans at the same time. More sites per region, or a model per region, are needed.
- **Within sites, the model does not beat the monthly baseline overall** (0.667 vs 0.689). It does beat it in 2021–23.
- **The signal is seasonal-scale.** It does not give a sharp warning just before a ban: onset AUC is 0.65, about the same as the monthly baseline.
- **Some splits rest on very few sites.** Within-site AUC in 2025–26 uses 2 sites, and 2020 and 2024 use 3.

## Deployment

The daily forecast does not use this model alone. It uses the ensemble of this model with LSTM, GRU and Transformer models trained on the same features (see `evaluation/README.md`). `export_deployment.py` writes both to `artifacts/best_model/env_model/`; this model is also the fallback if the deep models cannot run.

## SHAP for the deployed ensemble

`shap_ensemble.py` explains the deployed ensemble (artifacts/best_model/env_model/) on 2,000 sampled days with expected gradients, summing each feature over the 30-day window. Mean |SHAP| in ban probability:

| Feature | Mean \|SHAP\| |
|---|---|
| Site ban rate, previous year | 0.137 |
| Season (sine / cosine) | 0.050 / 0.049 |
| Sea temperature anomaly, 90-day | 0.026 |
| ONI | 0.015 |
| Rainfall anomaly, 90 / 60-day | 0.012 / 0.008 |
| Monthly site ban rate, 60/30-day sea temperature, 30-day rainfall | < 0.006 |

Warmer-than-usual sea temperature raises the predicted risk. Figures: `results/shap_ensemble_bar.png`, `results/shap_ensemble_beeswarm.png`.

## Usage

```bash
cd env_model
python train_env_model.py --loso
python compare_drivers.py
python shap_ensemble.py        # --plot-only redraws from saved values
cd ../evaluation
python retrain_leakfree.py
```
