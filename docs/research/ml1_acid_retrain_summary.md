# ML_1 Acid Retrain Summary (Literature Maturation Curves)

## Source graphs

- Coconut water maturation: **pH vs ascorbic acid (mg/100 mL)**
- Coconut water maturation: **pH vs titratable acidity (% citric acid)**
- Ascorbic unit conversion: `mg/100 mL / 1000 = % w/v`

## Results (held-out 20% test)

| Target | MAE | RMSE | R² |
|--------|----:|-----:|---:|
| Citric % | 0.0032 | 0.0041 | **0.9611** |
| Ascorbic % | 0.000103 | 0.000122 | **0.9697** |
| **OVERALL** | 0.0017 | 0.0029 | **0.9654** |

## Compared with previous Chapter 4 multi-output (random acid labels)

| Target | Old R² | New ML_1 R² |
|--------|-------:|------------:|
| Citric | ~0.77 | **0.9611** |
| Ascorbic | ~0.53 | **0.9697** |

## Files

- Dataset: `ML_1/dataset/combined_pH_temp_600.csv`
- Anchors: `ML_1/dataset/literature_maturation_anchors.csv`
- Model: `ML_1/models/random_forest_ph_temp.pkl`
- Metrics: `C:/Users/archchika/Desktop/research/docs/research/figures/ml1_acid_regression_metrics.csv`
