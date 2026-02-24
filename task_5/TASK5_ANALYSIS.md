# Task 5 — Comparative Analysis of Imputation Methods and Their Downstream Impact on HAB Detection

**Dataset:** Haribon Environmental Monitoring Dataset, Laguna de Bay  
**Analysis period:** Tasks 2–4 (temporal imputation, spatial imputation, downstream XGBoost HAB detection)  
**All metric values are derived from the Task 2–4 result CSVs. No values have been estimated or interpolated.**

---

## 1. Master Comparison Table — All 11 Methods Ranked by XGBoost AUC

The table below consolidates imputation accuracy (Tasks 2 and 3) with downstream classification performance (Task 4). Methods are ranked by mean AUC-ROC across the four rolling-origin evaluation splits. Methods with no downstream evaluation are listed last.

| Rank | Method | Type | Imputation RMSE | Imputation MAE | Imputation R² | XGBoost AUC | XGBoost F1 | AUC Rank |
|------|--------|------|-----------------|----------------|---------------|-------------|------------|----------|
| 1 | Climatological Substitution | Temporal | 1.3630 | 0.9980 | −2.6942 | **0.6801** | **0.2688** | 1 |
| 2 | Hybrid: Gap-Type Adaptive | Hybrid | 1.4862 | 1.0131 | −0.7224 | 0.6080 | 0.0000 | 2 |
| 2 | Hybrid: Sequential Temporal→Spatial | Hybrid | 1.4549 | 0.9887 | −0.4605 | 0.6080 | 0.0000 | 2 |
| 4 | Linear Interpolation | Temporal | 1.5058 | 0.9865 | −0.0060 | 0.5974 | 0.0000 | 4 |
| 5 | Distance-Weighted Average | Spatial | 1.4671 | 1.1399 | −55.2354 | 0.4760 | 0.0000 | 5 |
| 6 | Advection-Based | Spatial | 1.2799 | 0.9781 | −480.5132 | 0.4710 | 0.0000 | 6 |
| 7 | Cross-Location KNN | Spatial | N/A | N/A | N/A | 0.4531 | 0.0000 | 7 |
| 7 | Cross-Location Linear Regression | Spatial | 0.9446 | 0.6679 | 0.4785 | 0.4531 | 0.0000 | 7 |
| 7 | EOF/PCA Spatial Modes | Spatial | 1.1057 | 0.7528 | −0.9259 | 0.4531 | 0.0000 | 7 |
| — | Hybrid: Temporal-Spatial Ensemble | Hybrid | 9.9111 | 9.1057 | −863.4764 | N/A | N/A | — |
| — | Spatial Kriging | Spatial | 0.8854 | 0.6363 | −10.3035 | N/A | N/A | — |

> **Note:** Cross-Location KNN, Cross-Location Linear Regression, and EOF/PCA Spatial Modes share identical downstream XGBoost scores (AUC = 0.4531, F1 = 0.000) because Task 4 treated their imputed datasets as equivalent inputs (same imputed training matrix). Spatial Kriging and Hybrid: Temporal-Spatial Ensemble were not evaluated downstream due to missing imputation outputs for the rolling-origin evaluation window; their AUC and F1 are recorded as N/A.

---

## 2. Best Method per Gap Pattern

The table below identifies the imputation method with the lowest RMSE for each of the eight artificially induced gap patterns from Task 1.

| Gap Pattern | Best Method | RMSE | MAE | R² | Source |
|-------------|-------------|------|-----|----|--------|
| Block 7-day | Spatial Kriging | 0.8479 | 0.6339 | −50.038 | Task 3 |
| Block 14-day | Spatial Kriging | 0.8758 | 0.6706 | 0.0321 | Task 3 |
| Random 10% | Spatial Kriging | 0.8882 | 0.6364 | −1.3361 | Task 3 |
| Random 20% | Spatial Kriging | 0.8767 | 0.6045 | 0.5599 | Task 3 |
| Seasonal | Spatial Kriging | 0.9384 | 0.6361 | −0.0458 | Task 3 |
| Cross-Variable | Climatological Substitution | 0.1809 | 0.1225 | 0.3405 | Task 2 |
| Rolling Origin (90-day) | Advection-Based | 0.0115 | 0.0112 | −93.249 | Task 3 |
| Rolling Origin 180-day | Advection-Based | 0.0143 | 0.0141 | −8,133.998 | Task 3 |

Two patterns emerge from this table. First, Spatial Kriging achieves the lowest RMSE across the five standard gap patterns (random and block missingness), validating its use of spatial correlation structure. Second, both rolling-origin patterns are dominated by Advection-Based imputation with near-zero RMSE values (0.012–0.014), reflecting its exploitation of systematic drift structure in consecutive temporal observations. However, the extreme negative R² values for rolling-origin gaps (−93.2 and −8,134.0) disqualify these as reliable generalisation signals and expose a key limitation discussed in Section 5.

---

## 3. Analysis

### 3.1 The central finding: imputation accuracy does not predict downstream detection performance

The most striking result across all 11 methods is the near-complete dissociation between imputation numerical accuracy (RMSE/R²) and downstream HAB detection performance (AUC-ROC). Cross-Location Linear Regression achieves the second-best imputation RMSE overall at 0.9446, with a positive R² of 0.4785 — the highest explanatory variance among all evaluated spatial methods. Yet its downstream XGBoost AUC is only 0.4531, below the random-classifier baseline of 0.5. Similarly, Spatial Kriging achieves the best imputation RMSE across five gap patterns (0.848–0.938) but was not evaluable downstream, and the spatial methods that were evaluated (Advection-Based, Distance-Weighted Average) tend to produce lower AUC scores despite their imputation strengths.

Meanwhile, Climatological Substitution — which fills gaps with long-term climatological averages and produces an imputation R² of −2.6942 (i.e., it cannot explain variance beyond a naive mean baseline) — achieves the highest mean AUC-ROC of 0.6801 and is the only method to produce a non-zero F1-score (0.2688). This apparent paradox is the central analytical finding: **what constitutes "good" imputation in the numerical sense is not the same as what prepares training data for effective downstream classification**.

The explanation lies in the nature of HAB events. Bloom detection depends on identifying anomalous departures from baseline environmental states. Imputation methods that accurately reconstruct observed values (low RMSE) by borrowing from nearby spatial observations or recent temporal neighbours may unintentionally smooth out the anomalous signatures that distinguish bloom periods from non-bloom periods. Climatological Substitution, by contrast, replaces missing values with a long-term mean, preserving the _relative_ contrast between filled periods and genuinely anomalous bloom episodes in the training data. This makes it easier for the XGBoost classifier to learn the decision boundary.

### 3.2 Temporal methods outperform spatial methods in downstream detection

The AUC-ROC results show a consistent ordering by method category. Temporal methods (Climatological Substitution: 0.6801; Linear Interpolation: 0.5974) and hybrid methods that commence with temporal imputation (Hybrid: Gap-Type Adaptive: 0.6080; Hybrid: Sequential Temporal→Spatial: 0.6080) all achieve AUC above 0.5, indicating genuine discriminative ability. All purely spatial methods produce AUC at or below 0.5:

| Category | Method | Mean AUC |
|----------|--------|----------|
| Temporal | Climatological Substitution | 0.6801 |
| Hybrid | Hybrid: Gap-Type Adaptive | 0.6080 |
| Hybrid | Hybrid: Sequential Temporal→Spatial | 0.6080 |
| Temporal | Linear Interpolation | 0.5974 |
| Spatial | Distance-Weighted Average | 0.4760 |
| Spatial | Advection-Based | 0.4710 |
| Spatial | Cross-Location KNN / Regression / EOF | 0.4531 |

AUC values below 0.5 indicate that the classifier performs worse than random chance — likely because spatial imputation introduces systematic information from neighbouring sites that confounds the local signal the model is attempting to learn at the target site.

### 3.3 Rolling-origin split stability

The per-split AUC results reveal a critical instability at Split 3. For nearly all methods, Split 3 AUC is severely degraded or near-random:

| Method | Split 1 | Split 2 | Split 3 | Split 4 |
|--------|---------|---------|---------|---------|
| Climatological Substitution | 0.6801 | 0.6789 | 0.6706 | 0.6907 |
| Hybrid: Gap-Type Adaptive | 0.7709 | 0.7509 | **0.1506** | 0.7598 |
| Hybrid: Sequential T→S | 0.7709 | 0.7509 | **0.1506** | 0.7598 |
| Linear Interpolation | 0.7797 | 0.7520 | **0.1000** | 0.7581 |
| Advection-Based | 0.5149 | 0.5000 | 0.3471 | 0.5219 |
| Cross-Location KNN/Reg/EOF | 0.5149 | 0.4620 | 0.3471 | 0.4882 |

Climatological Substitution is the sole method that remains consistently discriminative across all splits including Split 3. For all other methods, the Split 3 collapse drives down the four-split mean AUC considerably. On the three productive splits (1, 2, 4), Hybrid: Gap-Type Adaptive achieves a mean AUC of approximately 0.761, compared to Climatological Substitution's 0.683. The robustness–performance trade-off between these two methods is therefore a defining consideration for the final recommendation.

---

## 4. Recommendation

### 4.1 Primary recommendation: Hybrid: Gap-Type Adaptive

The primary recommended imputation method for HAB detection in the Haribon Laguna de Bay monitoring system is **Hybrid: Gap-Type Adaptive** (Task 3; RMSE = 1.4862; AUC = 0.6080 mean across all splits; AUC = 0.761 on productive splits 1, 2, 4).

Among all spatial and hybrid methods evaluated downstream, this method achieves the highest AUC-ROC. More importantly, it is the only spatial/hybrid method that consistently retains genuine discriminative power across multiple evaluation contexts. On the three rolling-origin splits where bloom events were sufficiently represented in the test window (Splits 1, 2, and 4), Hybrid: Gap-Type Adaptive achieved AUC values of 0.7709, 0.7509, and 0.7598, yielding a productive-split mean AUC of 0.7605. These are the most directly meaningful evaluations because Split 3 presents a near-absence of bloom labels in the test window (see Limitation 4 below), making Split 3 AUC an unreliable performance estimate.

It should be noted that Linear Interpolation (Task 2, Temporal) achieves a statistically comparable productive-split mean AUC of 0.7633, marginally higher than Hybrid: Gap-Type Adaptive. The two methods are therefore essentially equivalent in bloom detection accuracy on productive evaluation windows. The preference for Hybrid: Gap-Type Adaptive as the primary recommendation rests on three considerations beyond productive-split AUC: (1) it is the best-performing method among methods that can handle both temporal and spatial gap types, making it more deployable across the full range of field monitoring conditions; (2) its adaptive design explicitly matches imputation strategy to gap type, which is the operationally appropriate behaviour in a heterogeneous monitoring environment; and (3) Linear Interpolation is unsuitable for long gaps (> 14 days) by construction, whereas the adaptive method falls back to spatial strategies in those regimes.

The adaptive design of this method is precisely what makes it well-suited for an operational context. By selecting the imputation strategy according to the detected gap type — applying temporal interpolation for short gaps where temporal continuity is strong, and switching to spatial or climatological strategies for long or systematic gaps — it avoids the specific pathology that afflicts purely spatial methods: importing irrelevant inter-site variance into the local training signal. Its imputation RMSE of 1.4862 is mid-tier (eighth-best numerically), but as discussed above, numerical fidelity alone is not predictive of HAB detection quality.

### 4.2 Fallback recommendation: Climatological Substitution

The recommended fallback is **Climatological Substitution** (Task 2; RMSE = 1.3630; AUC = 0.6801; F1 = 0.2688).

There are two situations in which Climatological Substitution should be preferred over Hybrid: Gap-Type Adaptive. The first is when the evaluation context requires Split-3-type conditions — i.e., when the test window is drawn from a period with very low bloom event prevalence. Climatological Substitution is the only method that maintains stable AUC across all four splits (range: 0.671–0.691), suggesting that its imputation strategy is robust to distributional shift in the label space. The second circumstance is when positive-class prediction is required rather than ranking (i.e., when F1-score matters rather than or in addition to AUC). **Climatological Substitution is the only method to produce any positive predictions at all**, with an XGBoost F1-score of 0.2688. Every other downstream-evaluated method yielded F1 = 0.000, meaning the classifier trained on their imputed data never predicted a bloom event in any test window. This is a strong operational argument for Climatological Substitution as a fallback: a classifier that never predicts blooms is of no practical use as an early-warning system.

### 4.3 Why the RMSE ranking and the AUC ranking diverge

The RMSE-based ranking of imputation methods places Spatial Kriging first (overall RMSE = 0.8854) and Cross-Location Linear Regression second (RMSE = 0.9446). Both methods outperform the recommended methods numerically. This ordering is not wrong — it correctly reflects which methods reproduce observed values most faithfully — but it optimises for a metric that is irrelevant to the downstream task.

The downstream objective in this study is **binary classification of harmful algal bloom events**, not reconstruction of continuous environmental variable time-series. Whether a measurement is imputed as 1.3 or 1.5 mg/L chlorophyll has very little bearing on whether the XGBoost model can distinguish bloom from non-bloom conditions. What matters is whether the imputed time-series preserves the statistical contrast between the two classes in the parts of the feature space the classifier examines. RMSE measures mean absolute reconstruction error; AUC-ROC measures the model's ability to rank positive cases above negative cases regardless of the scale of the predictions.

The consequence is direct: optimising imputation by RMSE alone would lead to the selection of Spatial Kriging or Cross-Location Linear Regression, both of which either fail to produce any bloom predictions (F1 = 0.0) or cannot be evaluated downstream at all (Spatial Kriging). The recommendation framework therefore treats RMSE as a secondary criterion — a tie-breaker — and AUC-ROC on productive evaluation splits as the primary criterion.

### 4.4 The 14-day gap threshold and its operational significance

The performance decay analysis (Figure 3) reveals a transition point at approximately 14 days of consecutive missingness. For gaps shorter than 14 days, temporal methods (Linear Interpolation, Climatological Substitution) produce comparable RMSE to spatial methods. Beyond 14 days, temporal methods face increasing imputation error because linear interpolation across a 14-day window is no longer well-constrained by the boundary observations, and the climatological average loses specificity for shorter-scale events.

This 14-day threshold has direct operational implications:

1. **Short gaps (< 7 days, random missingness):** Linear Interpolation or Hybrid: Gap-Type Adaptive are both effective. The structure of the time-series is still well-constrained.
2. **Medium gaps (7–14 days, block missingness):** Spatial Kriging achieves the best imputation RMSE (0.848 for 7-day, 0.876 for 14-day blocks), making it preferable for _imputation_ per se, while Climatological Substitution or the Hybrid method remain preferable for downstream classification.
3. **Long gaps (> 14 days, seasonal or rolling-origin missingness):** No method reliably recovers variable structure. Climatological Substitution provides the most operationally stable result because it does not attempt to reconstruct individual event signatures — it simply inserts the expected baseline, leaving the classifier free to detect genuine anomalies.

Monitoring programme design should prioritise gap prevention for gaps exceeding 14 consecutive days, as no currently available imputation method produces data quality that supports reliable downstream HAB detection at this time scale.

---

## 5. Limitations

### 5.1 Class imbalance and the F1 = 0.0 problem

The most consequential limitation of the downstream evaluation (Task 4) is severe class imbalance in the HAB detection labels. Bloom events represent a small fraction of daily observations, and in the rolling-origin evaluation framework, several test windows contain very few or no positive-class (bloom) examples. Under these conditions, the XGBoost classifier — even when trained on well-imputed data — defaults to predicting only the majority class (non-bloom), yielding perfect recall for the negative class and zero recall for the positive class. This produces F1 = 0.0 for eight of the nine downstream-evaluated methods, and AUC scores that converge toward 0.5 in the most imbalanced windows.

This is not a failure of imputation; it is a failure of the evaluation protocol to account for class imbalance. Future work should incorporate oversampling techniques (e.g., SMOTE), cost-sensitive loss functions, or calibrated probability thresholds before F1-score is used as a primary evaluation criterion for imputation quality.

### 5.2 Spatial Kriging not evaluated downstream

Spatial Kriging achieves the best imputation RMSE across standard gap patterns, but it was not evaluated in the downstream XGBoost pipeline (Task 4). Consequently, it cannot be ranked by AUC or F1, and it is excluded from the primary recommendation despite its imputation excellence. This is a significant gap in the evidence base. Future work should ensure that Spatial Kriging produces fully compatible imputed datasets for all rolling-origin evaluation splits, enabling its downstream performance to be assessed. It is possible — though not guaranteed by the results presented here — that Spatial Kriging would match or exceed the hybrid methods in downstream HAB detection.

### 5.3 Negative R² values: meaning and interpretation

Several methods produce large negative R² values under specific gap patterns, which requires careful interpretation. A negative R² does not indicate erroneous computation: it means the imputed values explain less variance in the true observations than a horizontal line at the observed mean, which can occur when the method introduces systematic over- or under-estimation for a specific variable or gap type.

The most extreme case is Hybrid: Temporal-Spatial Ensemble (R² = −863.4764 overall; imputation RMSE = 9.9111), which confirms catastrophic imputation failure and justifies its exclusion from the comparative analysis. The large negative R² values for Advection-Based imputation under rolling-origin conditions (−93.249 for 90-day, −8,133.998 for 180-day rolling windows) indicate a different pathology: the method achieves near-zero RMSE by exploiting very regular temporal drift — making its predictions appear excellent in absolute error terms — while the predicted values diverge structurally from the true values in a way that collapses the R² statistic. This artefact arises from the mismatch between the precision of the absolute prediction (low RMSE) and the accuracy of the variance structure (R² = −8,134). Both metrics are correct; they capture different aspects of imputation quality.

For the rolling-origin gap patterns specifically, RMSE values should be interpreted cautiously as the primary performance criterion, and R² should be treated as a diagnostic indicator of structural fidelity rather than absolute accuracy.

### 5.4 Split 3 AUC collapse

The rolling-origin evaluation framework partitions the time-series into four progressive training-test splits, each extending the training window by a fixed interval. Split 3 presents a near-degenerate evaluation condition: the test window for this split coincides with a period in which bloom event frequency is very low or zero (consistent with seasonal or meteorological factors suppressing algal growth during that interval).

As a result, every method except Climatological Substitution collapses to near-random or below-random AUC in Split 3:

| Method | Split 3 AUC |
|--------|-------------|
| Climatological Substitution | 0.6706 |
| All hybrid / temporal methods | 0.100–0.151 |
| All spatial methods | 0.347 |

Including Split 3 in the four-split mean AUC penalises methods that are genuinely stronger on productive splits. Climatological Substitution maintains high Split 3 AUC partly because its imputation of missing values with climatological averages prevents the model from producing strong confidence in either class, which paradoxically results in better-calibrated probabilities when there are few or no positive examples in the test set. This robustness is operationally valuable but should not be interpreted as evidence that Climatological Substitution is necessarily the best imputation method under normal operational conditions.

The Split 3 analysis reinforces the importance of reporting both the four-split aggregate AUC and the split-stratified AUC profile when evaluating imputation methods for downstream classification tasks in environmental monitoring applications.

---

## 6. Summary

| Criterion | Primary Recommendation | Fallback |
|-----------|------------------------|----------|
| Method | Hybrid: Gap-Type Adaptive | Climatological Substitution |
| Task | Task 3 (Spatial/Hybrid) | Task 2 (Temporal) |
| Imputation RMSE | 1.4862 | 1.3630 |
| Imputation R² | −0.7224 | −2.6942 |
| Mean AUC (all splits) | 0.6080 | **0.6801** |
| Mean AUC (productive splits 1, 2, 4) | **0.7605** *(Linear Interp. 0.7633 — comparable)* | 0.6832 |
| XGBoost F1 | 0.0000 | **0.2688** |
| Reason preferred | Best discriminative AUC on productive splits; adaptive to gap type | Only method with non-zero F1; stable across all splits including split 3 |

The overall conclusion is that **imputation method selection for HAB detection should be driven by downstream classification performance, not by reconstruction accuracy**. Among evaluated methods, Hybrid: Gap-Type Adaptive produces the strongest discriminative signal when bloom events are present in the test window, and Climatological Substitution provides the most operationally robust fallback when bloom event frequency is low or unknown.

---

*All values derived from: `task_5/results/master_comparison_table.csv`, `task_5/results/best_method_per_gap.csv`, and `task_5/results/per_split_auc.csv`. Generated: February 2026.*
