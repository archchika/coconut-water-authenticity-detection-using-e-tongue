"""
Compute overall (common) R² / MAE / RMSE across all three composition outputs,
in the same style as a single-target report (e.g. Siva thesis: one MAE + one R²).

Also computes the first canonical correlation (CCA ρ₁) between the sensor input
block and the composition output block as a single input–output association.

Outputs:
  docs/research/figures/chapter4_overall_regression_metrics.csv
  docs/research/overall_ml_results_summary.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cross_decomposition import CCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "ML_2" / "dataset" / "combined_sensors_sugar.csv"
OUT_DIR = ROOT / "docs" / "research" / "figures"
OUT_MD = ROOT / "docs" / "research" / "overall_ml_results_summary.md"
DESKTOP_DIR = Path.home() / "Desktop" / "chapter4_graphs"

FEATURE_COLS = ["pH", "TDS", "temperature", "turbidity"]
TARGET_COLS = ["sugar_pct", "citric_acid_pct", "ascorbic_acid_pct"]
TARGET_LABELS = ["Sugar %", "Citric %", "Ascorbic %"]

RANDOM_STATE = 42
TEST_SIZE = 0.2
MODEL_PARAMS = {"n_estimators": 200, "max_depth": 12, "random_state": RANDOM_STATE}


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    data = df[FEATURE_COLS + TARGET_COLS].dropna().copy()
    X = data[FEATURE_COLS].astype(float).values
    y = data[TARGET_COLS].astype(float).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    model = RandomForestRegressor(**MODEL_PARAMS)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    rows = []
    for i, label in enumerate(TARGET_LABELS):
        rows.append(
            {
                "Scope": label,
                "MAE": float(mean_absolute_error(y_test[:, i], y_pred[:, i])),
                "RMSE": float(np.sqrt(mean_squared_error(y_test[:, i], y_pred[:, i]))),
                "R2": float(r2_score(y_test[:, i], y_pred[:, i])),
            }
        )

    # Uniform average across the three outputs (sklearn multi-output default)
    overall = {
        "Scope": "OVERALL (sugar + citric + ascorbic)",
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "R2": float(r2_score(y_test, y_pred)),
    }
    rows.append(overall)

    # CCA: single common correlation between input block and output block
    x_s = StandardScaler().fit_transform(X)
    y_s = StandardScaler().fit_transform(y)
    n_comp = min(len(FEATURE_COLS), len(TARGET_COLS))
    cca = CCA(n_components=n_comp, max_iter=500)
    x_c, y_c = cca.fit_transform(x_s, y_s)
    rho1 = float(np.corrcoef(x_c[:, 0], y_c[:, 0])[0, 1])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    csv_path = OUT_DIR / "chapter4_overall_regression_metrics.csv"
    metrics_df.to_csv(csv_path, index=False)
    metrics_df.to_csv(DESKTOP_DIR / "chapter4_overall_regression_metrics.csv", index=False)

    # Also refresh per-target chapter4 file so both stay aligned
    per_target = metrics_df[metrics_df["Scope"] != overall["Scope"]].rename(
        columns={"Scope": "Target"}
    )
    per_target.to_csv(OUT_DIR / "chapter4_regression_metrics.csv", index=False)
    per_target.to_csv(DESKTOP_DIR / "chapter4_regression_metrics.csv", index=False)

    md = f"""# Overall ML Results (Composition) — Monthly Progress

Same reporting style as a single-target thesis (one MAE + one R²), applied to **three**
composition outputs by taking the **uniform average** across sugar, citric, and ascorbic.

## Dataset / model

- Data: `ML_2/dataset/combined_sensors_sugar.csv` (N={len(data)})
- Split: 80/20, `random_state={RANDOM_STATE}`
- Model: `RandomForestRegressor(n_estimators=200, max_depth=12)`
- Inputs: pH, TDS, temperature, turbidity
- Outputs: sugar %, citric %, ascorbic %

## Showcase table (use this in report)

| Scope | MAE | RMSE | R² |
|-------|----:|-----:|---:|
| Sugar % | {rows[0]['MAE']:.4f} | {rows[0]['RMSE']:.4f} | {rows[0]['R2']:.4f} |
| Citric % | {rows[1]['MAE']:.6f} | {rows[1]['RMSE']:.6f} | {rows[1]['R2']:.4f} |
| Ascorbic % | {rows[2]['MAE']:.6f} | {rows[2]['RMSE']:.6f} | {rows[2]['R2']:.4f} |
| **OVERALL (all 3 outputs)** | **{overall['MAE']:.4f}** | **{overall['RMSE']:.4f}** | **{overall['R2']:.4f}** |

**Overall R² = {overall['R2']:.4f}**  (~{overall['R2'] * 100:.1f}% variance explained on average)  
**Overall MAE = {overall['MAE']:.4f}** (mean of the three target MAEs)

## Common input–output correlation (CCA)

First canonical correlation between sensors and composition:

| Metric | Value |
|--------|------:|
| CCA ρ₁ (inputs ↔ outputs) | **{rho1:.4f}** |

This is the single “common correlation” between the input set and the output set
(not one pairwise Pearson value).

## How to write this (like Siva thesis)

> The multi-output Random Forest model achieved an **overall R² of {overall['R2']:.4f}**
> and an **overall MAE of {overall['MAE']:.4f}** across sugar, citric acid, and ascorbic acid
> predictions on the held-out test set. The first canonical correlation between sensor inputs
> and composition outputs was **ρ₁ = {rho1:.4f}**.

Final authenticity decision uses **pH + sugar + citric + ascorbic** natural-range
screening (`docs/research/authenticity_results_summary.md`).

## Files

- `{csv_path.as_posix()}`
- `{OUT_MD.as_posix()}`
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(metrics_df.to_string(index=False))
    print(f"\nCCA rho1 = {rho1:.4f}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
