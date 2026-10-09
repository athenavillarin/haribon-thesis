# Environment-Driven HAB Model

Logistic regression on slow-moving environmental drivers plus each site's ban history.

## Why this model

`evaluation/baselines.py` showed that the existing models mostly recognised sites:

- Their AUC within a single site was 0.45–0.61, which is close to chance.
- A lookup of each site's monthly ban rate scored higher (0.67).
- The top SHAP features (`mlotst`, `NDVI_daily`, `so`, `thetao`) vary more between sites than within them, so they act as site fingerprints.

Changes made here:

- **Site-relative anomalies.** Sea temperature and rainfall are compared with each site's monthly climatology and scaled by that site's standard deviation.
- **30/60/90-day rolling means, season and ENSO.** ONI is lagged 3 months so it is available on the date it is used. These slow-moving drivers were the only ones with a consistent within-site signal; satellite chlorophyll showed none.
- **Site ban history from earlier years only.** Each row's history features come from years before its own.
- **Testing-delay-aware weights.** Shellfish testing takes about 2 weeks, so the 14 days before a ban starts and the last 14 days of a ban get weight 0.3. Days with a real bulletin get weight 3. Weights use training labels only.
- **No look-ahead in features.** Gaps are forward-filled for up to 14 days, then filled from training-period climatology. Every statistic uses training dates only.
- **A small linear model.** The data hold about 130 ban onsets. XGBoost on about 100 features scored lower within sites (0.49).

## Results (6 rolling-origin splits, mean; all models scored on the same rows)

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Yesterday's label (persistence) | 0.995 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.788 | 0.500 | 0.636 | 0.630 |
| Site rate by month (climatology) | 0.751 | 0.667 | 0.691 | 0.669 |
| History features only | 0.770 | 0.664 | 0.606 | 0.596 |
| Environment only | 0.692 | 0.618 | 0.591 | 0.555 |
| **History + environment** | **0.831** | 0.642 | 0.621 | 0.605 |
| LSTM (retrained leak-free) | 0.698 | 0.447 | 0.639 | 0.624 |
| GRU (retrained leak-free) | 0.733 | 0.508 | 0.693 | 0.673 |
| Transformer (retrained leak-free) | 0.722 | 0.588 | 0.707 | 0.698 |
| XGBoost (retrained leak-free) | 0.736 | 0.480 | 0.673 | 0.663 |

The onset columns score whether a ban starts within 7 or 14 days, counting only days that are not already under a ban. The existing model types were retrained without look-ahead by `evaluation/retrain_leakfree.py`; see `evaluation/README.md`.

**Within-site AUC by split:**

| Split (test year) | Sites scored | Climatology | Environment only | History + environment |
|---|---|---|---|---|
| 1 (2020) | 1 | 0.849 | 0.876 | 0.866 |
| 2 (2021) | 2 | 0.664 | 0.628 | 0.640 |
| 3 (2022) | 5 | 0.606 | 0.780 | 0.770 |
| 4 (2023) | 5 | 0.666 | 0.845 | 0.851 |
| 5 (2024) | 1 | 0.338 | 0.235 | 0.196 |
| 6 (2025–26) | 1 | 0.880 | 0.347 | 0.530 |

In splits 3–4, five sites have both banned and clear days in the test year. In those splits the environmental features clearly beat seasonal history. In splits 5–6 only Matarinao Bay has both, and the environmental signal fails there.

**Leave-one-site-out (environment only):** the model trains on six sites up to 2021 and is tested on the seventh site from 2022 on, so neither that site nor that period is seen in training.

| Site | AUC |
|---|---|
| Gigantes Islands | 0.769 |
| Pilar | 0.755 |
| Sapian Bay | 0.752 |
| Roxas City | 0.751 |
| President Roxas | 0.693 |
| Matarinao Bay | 0.603 |
| Dumanquillas Bay | n/a (banned every day after 2021) |

**Strongest drivers (standardized coefficients, final split):**

- site's ban rate over the previous year: +0.96
- 60-day rainfall anomaly: +0.47
- 90-day sea temperature anomaly: +0.44
- season (`doy_sin`): −0.41

## Limitations

- The environmental signal is seasonal-scale. It does not give a sharp warning just before a ban: onset AUC is 0.61. No model clearly beats the monthly baseline (0.67) on onset; the retrained models land between 0.62 and 0.70.
- Within-site AUC in splits 1, 5 and 6 rests on a single site.
- The original training scripts and `ensemble_data.py` still impute with future values. The saved models' scores are therefore optimistic; for example, the Transformer drops from 0.846 to 0.722 when retrained without look-ahead.
- More sites with recurring seasonal blooms would add onset events, which are the limiting factor.

## Usage

```bash
cd env_model
python train_env_model.py --loso
cd ../evaluation
python baselines.py
```
