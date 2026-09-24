# Overall ML Results (Composition) — Monthly Progress

Same reporting style as a single-target thesis (one MAE + one R²), applied to **three**
composition outputs by taking the **uniform average** across sugar, citric, and ascorbic.

## Dataset / model

- Data: `ML_2/dataset/combined_sensors_sugar.csv` (N=482)
- Split: 80/20, `random_state=42`
- Model: `RandomForestRegressor(n_estimators=200, max_depth=12)`
- Inputs: pH, TDS, temperature, turbidity
- Outputs: sugar %, citric %, ascorbic %

## Showcase table (use this in report)

| Scope | MAE | RMSE | R² |
|-------|----:|-----:|---:|
| Sugar % | 0.9007 | 1.3317 | 0.9044 |
| Citric % | 0.004467 | 0.006969 | 0.9226 |
| Ascorbic % | 0.000995 | 0.002554 | 0.6140 |
| **OVERALL (all 3 outputs)** | **0.3021** | **0.7688** | **0.8137** |

**Overall R² = 0.8137**  (~81.4% variance explained on average)  
**Overall MAE = 0.3021** (mean of the three target MAEs)

## Common input–output correlation (CCA)

First canonical correlation between sensors and composition:

| Metric | Value |
|--------|------:|
| CCA ρ₁ (inputs ↔ outputs) | **0.8812** |

This is the single “common correlation” between the input set and the output set
(not one pairwise Pearson value).

## How to write this (like Siva thesis)

> The multi-output Random Forest model achieved an **overall R² of 0.8137**
> and an **overall MAE of 0.3021** across sugar, citric acid, and ascorbic acid
> predictions on the held-out test set. The first canonical correlation between sensor inputs
> and composition outputs was **ρ₁ = 0.8812**.

Final authenticity decision uses **pH + sugar + citric + ascorbic** natural-range
screening (`docs/research/authenticity_results_summary.md`).

## Files

- `C:/Users/archchika/Desktop/research/docs/research/figures/chapter4_overall_regression_metrics.csv`
- `C:/Users/archchika/Desktop/research/docs/research/overall_ml_results_summary.md`
