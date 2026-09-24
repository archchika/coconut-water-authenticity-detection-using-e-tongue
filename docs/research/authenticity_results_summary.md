# Authenticity vs Adulteration — Final System Results

## Decision rule (live system)

A sample is **authentic** only if **pH + sugar + citric + ascorbic** all fall inside natural ranges; otherwise **adulterated**.

| Parameter | Natural range |
|-----------|---------------|
| pH | 4.7 – 6.32 |
| Sugar % | 1.8 – 7.0 |
| Citric % | 0.04 – 0.15 |
| Ascorbic % | 0.0008 – 0.0035 |

pH is both a **sensor input** to ML and part of the **final authenticity decision**.

## Dataset

- Source: June 30 prototype validation (`backend/readings/data/june30_validation.json`)
- **100 Natural** + **100 Artificial** samples (balanced)

## Showcase metrics (Natural vs Artificial ground truth)

| Metric | Value |
|--------|------:|
| Accuracy | **91.50%** |
| Precision (Authentic) | 100.00% |
| Recall (Authentic) | 83.00% |
| F1 (Authentic) | 90.71% |
| N | 200 |

### Confusion matrix

```
                Predicted Authentic | Predicted Adulterated
Actual Authentic           83                  17
Actual Adulterated          0                 100
```

## Supporting composition accuracy (lab vs ML)

| Parameter | Accuracy vs lab |
|-----------|----------------:|
| Overall (pH + sugar + citric + ascorbic) | 86.98% |
| pH | 95.07% |
| Sugar | 87.0% |
| Citric | 84.35% |
| Ascorbic | 81.49% |

## How to present this

1. **ML quality:** MAE / R² for sugar, citric, ascorbic (regression).
2. **Final product result:** Accuracy / Precision / Recall / F1 for Authentic vs Adulterated (this file).

Files written:
- `C:/Users/archchika/Desktop/research/docs/research/figures/chapter4_authenticity_metrics.csv`
- `C:/Users/archchika/Desktop/research/docs/research/authenticity_results_summary.md`
