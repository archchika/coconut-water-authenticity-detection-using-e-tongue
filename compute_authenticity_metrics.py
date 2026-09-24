"""
Compute final Authentic vs Adulterated metrics for monthly progress / Chapter 4.

Uses the balanced June 30 prototype validation set (100 Natural + 100 Artificial).

Two ground-truth definitions are reported:
  A) Sample type: Natural → authentic, Artificial → adulterated
  B) Lab composition screened with the same natural ranges as the live system

Predicted label = ML composition screened with NATURAL_RANGES
  (sugar 1.8–7.0, citric 0.04–0.15, ascorbic 0.00015–0.00035).

Outputs:
  docs/research/figures/chapter4_authenticity_metrics.csv
  docs/research/authenticity_results_summary.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from readings.ml_inference import NATURAL_RANGES, classify_authenticity  # noqa: E402

JSON_PATH = ROOT / "backend" / "readings" / "data" / "june30_validation.json"
OUT_CSV = ROOT / "docs" / "research" / "figures" / "chapter4_authenticity_metrics.csv"
OUT_MD = ROOT / "docs" / "research" / "authenticity_results_summary.md"
DESKTOP_CSV = Path.home() / "Desktop" / "chapter4_graphs" / "chapter4_authenticity_metrics.csv"


def _metrics(y_true: list[str], y_pred: list[str], positive: str = "authentic") -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p != positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    n = len(y_true)
    acc = (tp + tn) / n if n else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "Accuracy": round(acc, 4),
        "Precision_Authentic": round(prec, 4),
        "Recall_Authentic": round(rec, 4),
        "F1_Authentic": round(f1, 4),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "N_test": n,
        "N_authentic_actual": sum(1 for t in y_true if t == positive),
        "N_adulterated_actual": sum(1 for t in y_true if t != positive),
    }


def main() -> None:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    samples = payload["samples"]
    param_metrics = payload.get("metrics", {})

    true_type: list[str] = []
    true_lab: list[str] = []
    pred_ml: list[str] = []

    for s in samples:
        true_type.append("authentic" if s["type"] == "Natural" else "adulterated")
        true_lab.append(
            classify_authenticity(
                s["lab_sugar_pct"],
                s["lab_citric_pct"],
                s["lab_ascorbic_pct"],
                ph=s["lab_ph"],
            )
        )
        pred_ml.append(
            classify_authenticity(
                s["ml_sugar_pct"],
                s["ml_citric_pct"],
                s["ml_ascorbic_pct"],
                ph=s["ml_ph"],
            )
        )

    m_type = _metrics(true_type, pred_ml)
    m_lab = _metrics(true_lab, pred_ml)

    # Primary showcase row = type-based (balanced 100/100 Natural vs Artificial)
    primary = {**m_type, "GroundTruth": "Natural_vs_Artificial"}
    secondary = {**m_lab, "GroundTruth": "Lab_composition_ranges"}

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "GroundTruth",
        "Accuracy",
        "Precision_Authentic",
        "Recall_Authentic",
        "F1_Authentic",
        "TP",
        "TN",
        "FP",
        "FN",
        "N_test",
        "N_authentic_actual",
        "N_adulterated_actual",
    ]
    lines = [",".join(header)]
    for row in (primary, secondary):
        lines.append(",".join(str(row[h]) for h in header))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    DESKTOP_CSV.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP_CSV.write_text(OUT_CSV.read_text(encoding="utf-8"), encoding="utf-8")

    conf_type = (
        f"                Predicted Authentic | Predicted Adulterated\n"
        f"Actual Authentic          {m_type['TP']:3d}                 {m_type['FN']:3d}\n"
        f"Actual Adulterated        {m_type['FP']:3d}                 {m_type['TN']:3d}"
    )

    md = f"""# Authenticity vs Adulteration — Final System Results

## Decision rule (live system)

A sample is **authentic** only if **pH + sugar + citric + ascorbic** all fall inside natural ranges; otherwise **adulterated**.

| Parameter | Natural range |
|-----------|---------------|
| pH | {NATURAL_RANGES['ph'][0]} – {NATURAL_RANGES['ph'][1]} |
| Sugar % | {NATURAL_RANGES['sugar'][0]} – {NATURAL_RANGES['sugar'][1]} |
| Citric % | {NATURAL_RANGES['citric'][0]} – {NATURAL_RANGES['citric'][1]} |
| Ascorbic % | {NATURAL_RANGES['ascorbic'][0]} – {NATURAL_RANGES['ascorbic'][1]} |

pH is both a **sensor input** to ML and part of the **final authenticity decision**.

## Dataset

- Source: June 30 prototype validation (`backend/readings/data/june30_validation.json`)
- **100 Natural** + **100 Artificial** samples (balanced)

## Showcase metrics (Natural vs Artificial ground truth)

| Metric | Value |
|--------|------:|
| Accuracy | **{m_type['Accuracy'] * 100:.2f}%** |
| Precision (Authentic) | {m_type['Precision_Authentic'] * 100:.2f}% |
| Recall (Authentic) | {m_type['Recall_Authentic'] * 100:.2f}% |
| F1 (Authentic) | {m_type['F1_Authentic'] * 100:.2f}% |
| N | {m_type['N_test']} |

### Confusion matrix

```
{conf_type}
```

## Supporting composition accuracy (lab vs ML)

| Parameter | Accuracy vs lab |
|-----------|----------------:|
| Overall (pH + sugar + citric + ascorbic) | {param_metrics.get('overall_accuracy_pct', '—')}% |
| pH | {param_metrics.get('ph_accuracy_pct', '—')}% |
| Sugar | {param_metrics.get('parameters', {}).get('sugar_pct', {}).get('accuracy_pct', '—')}% |
| Citric | {param_metrics.get('parameters', {}).get('citric_pct', {}).get('accuracy_pct', '—')}% |
| Ascorbic | {param_metrics.get('parameters', {}).get('ascorbic_pct', {}).get('accuracy_pct', '—')}% |

## How to present this

1. **ML quality:** MAE / R² for sugar, citric, ascorbic (regression).
2. **Final product result:** Accuracy / Precision / Recall / F1 for Authentic vs Adulterated (this file).

Files written:
- `{OUT_CSV.as_posix()}`
- `{OUT_MD.as_posix()}`
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print("Authenticity metrics (Natural/Artificial ground truth):")
    for k, v in m_type.items():
        print(f"  {k}: {v}")
    print()
    print("Authenticity metrics (lab-range ground truth):")
    for k, v in m_lab.items():
        print(f"  {k}: {v}")
    print()
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {DESKTOP_CSV}")


if __name__ == "__main__":
    main()
