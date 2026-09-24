"""
Write ML_1 citric/ascorbic regression metrics after literature-based retrain.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from ML_1.load_dataset import TARGET_COLUMNS, load_xy  # noqa: E402
from ML_1.train_model import MODEL_PARAMS, RANDOM_STATE, TEST_SIZE  # noqa: E402

OUT_CSV = ROOT / "docs" / "research" / "figures" / "ml1_acid_regression_metrics.csv"
OUT_MD = ROOT / "docs" / "research" / "ml1_acid_retrain_summary.md"
DESKTOP = Path.home() / "Desktop" / "chapter4_graphs"


def main() -> None:
    X, y = load_xy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    model = RandomForestRegressor(**MODEL_PARAMS)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    rows = []
    for i, name in enumerate(TARGET_COLUMNS):
        rows.append(
            {
                "Target": name,
                "MAE": float(mean_absolute_error(y_test[:, i], y_pred[:, i])),
                "RMSE": float(np.sqrt(mean_squared_error(y_test[:, i], y_pred[:, i]))),
                "R2": float(r2_score(y_test[:, i], y_pred[:, i])),
            }
        )
    rows.append(
        {
            "Target": "OVERALL (citric + ascorbic)",
            "MAE": float(mean_absolute_error(y_test, y_pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "R2": float(r2_score(y_test, y_pred)),
        }
    )
    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    df.to_csv(DESKTOP / OUT_CSV.name, index=False)

    cit = rows[0]
    asc = rows[1]
    overall = rows[2]
    md = f"""# ML_1 Acid Retrain Summary (Literature Maturation Curves)

## Source graphs

- Coconut water maturation: **pH vs ascorbic acid (mg/100 mL)**
- Coconut water maturation: **pH vs titratable acidity (% citric acid)**
- Ascorbic unit conversion: `mg/100 mL / 1000 = % w/v`

## Results (held-out 20% test)

| Target | MAE | RMSE | R² |
|--------|----:|-----:|---:|
| Citric % | {cit['MAE']:.4f} | {cit['RMSE']:.4f} | **{cit['R2']:.4f}** |
| Ascorbic % | {asc['MAE']:.6f} | {asc['RMSE']:.6f} | **{asc['R2']:.4f}** |
| **OVERALL** | {overall['MAE']:.4f} | {overall['RMSE']:.4f} | **{overall['R2']:.4f}** |

## Compared with previous Chapter 4 multi-output (random acid labels)

| Target | Old R² | New ML_1 R² |
|--------|-------:|------------:|
| Citric | ~0.77 | **{cit['R2']:.4f}** |
| Ascorbic | ~0.53 | **{asc['R2']:.4f}** |

## Files

- Dataset: `ML_1/dataset/combined_pH_temp_600.csv`
- Anchors: `ML_1/dataset/literature_maturation_anchors.csv`
- Model: `ML_1/models/random_forest_ph_temp.pkl`
- Metrics: `{OUT_CSV.as_posix()}`
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(df.to_string(index=False))
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
