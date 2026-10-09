# Environment-Driven HAB Model

Logistic regression on slow-moving environmental drivers plus each site's ban history.

## Why this model

`evaluation/baselines.py` showed that the existing models mostly recognised sites:

- Their AUC within a single site was 0.47–0.59, which is close to chance.
- A lookup of each site's monthly ban rate scored higher (0.66).
- The top SHAP features (`mlotst`, `NDVI_daily`, `so`, `thetao`) vary more between sites than within them, so they act as site fingerprints.

Changes made here:

- **Site-relative anomalies.** Each variable is compared with its own site's monthly climatology and scaled by that site's standard deviation, using training dates only.
- **Rolling and lagged windows** of 7–90 days, plus the ENSO index (ONI, lagged 2 months).
- **Testing-delay-aware weights.** Shellfish testing takes about 2 weeks, so the 14 days before a ban starts and the last 14 days of a ban get weight 0.3. Days with a real bulletin get weight 3.
- **A small linear model.** The data hold about 130 ban onsets. XGBoost on about 100 features scored lower within sites (0.49).

## Results (6 rolling-origin splits, mean)

| Model | All sites | Within site | Onset 7d | Onset 14d |
|---|---|---|---|---|
| Yesterday's label (persistence) | 0.995 | 0.991 | 0.500 | 0.500 |
| Site rate, last 365 days | 0.785 | 0.500 | 0.636 | 0.630 |
| Site rate by month (climatology) | 0.749 | 0.661 | 0.691 | 0.669 |
| History features only | 0.745 | 0.661 | 0.657 | 0.636 |
| Environment only | 0.687 | 0.607 | 0.602 | 0.565 |
| **History + environment** | **0.787** | **0.667** | **0.708** | **0.686** |
| LSTM (existing) | 0.683 | 0.470 | 0.575 | 0.577 |
| GRU (existing) | 0.674 | 0.593 | 0.640 | 0.649 |
| Transformer (existing) | 0.845 | 0.470 | 0.781 | 0.774 |
| XGBoost (existing) | 0.727 | 0.479 | 0.677 | 0.670 |

The onset columns score whether a ban starts within 7 or 14 days, counting only days that are not already under a ban.

**Leave-one-site-out (environment only, the held-out site is never seen in training):**

| Site | AUC |
|---|---|
| Dumanquillas Bay | 0.747 |
| Gigantes Islands | 0.619 |
| Matarinao Bay | 0.618 |
| Pilar | 0.715 |
| President Roxas | 0.766 |
| Roxas City | 0.807 |
| Sapian Bay | 0.674 |

**Strongest drivers (standardized coefficients, final split):**

- the site's ban rate for that month: +1.27
- 90-day sea temperature anomaly: +0.83
- ONI (El Niño): +0.58
- 90-day rainfall anomaly: +0.41

Satellite chlorophyll showed no within-site signal and is not used.

## Limitations

- Within-site AUC in splits 5–6 rests on one site (Matarinao Bay). In 2024–26, every other site was entirely banned or entirely clear.
- The environmental signal is seasonal-scale, not a sharp warning just before a ban.
- More sites with recurring seasonal blooms would add onset events, which are the limiting factor.

## Usage

```bash
cd env_model
python train_env_model.py --loso
cd ../evaluation
python baselines.py
```
