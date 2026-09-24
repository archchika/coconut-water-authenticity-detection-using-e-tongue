"""
Generate ML_1 training data from coconut-water maturation literature curves.

Anchors digitized from:
  1) pH vs Ascorbic Acid (mg/100 mL) during maturation (4–12 months)
  2) pH vs Titratable Acidity (% citric acid) during maturation (4–12 months)

Ascorbic conversion: mg/100 mL → % w/v  (divide by 1000).

Outputs:
  - ML_1/dataset/literature_maturation_anchors.csv
  - ML_1/dataset/combined_pH_temp_600.csv   (ready for ML_1 train_model.py)
  - also refreshes root citric/ascorbic CSVs used by merge_datasets.py

Run from project root:
  python generate_coconut_acid_literature_dataset.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
ML1_DIR = ROOT / "ML_1" / "dataset"
OUT_COMBINED = ML1_DIR / "combined_pH_temp_600.csv"
OUT_ANCHORS = ML1_DIR / "literature_maturation_anchors.csv"
OUT_CITRIC = ROOT / "citric_pH_temp_synthetic_600.csv"
OUT_ASCORBIC = ROOT / "ascorbic_pH_temp_synthetic_600.csv"

# Digitized anchors: maturity_months, pH, citric_%w/v, ascorbic_mg_per_100mL
MATURATION_ANCHORS = np.array(
    [
        # month, pH_citric_curve, citric_pct, pH_ascorbic_curve, ascorbic_mg_100mL
        [4.0, 4.75, 0.130, 4.78, 3.20],
        [6.0, 5.05, 0.110, 5.10, 2.50],
        [8.0, 5.35, 0.090, 5.35, 1.85],
        [10.0, 5.62, 0.075, 5.55, 1.25],
        [12.0, 5.90, 0.060, 5.71, 0.95],
    ],
    dtype=float,
)

DEFAULT_N = 600
DEFAULT_SEED = 42


def _interp(month: float, x_col: int, y_col: int) -> float:
    return float(np.interp(month, MATURATION_ANCHORS[:, 0], MATURATION_ANCHORS[:, y_col]))


def save_anchors(path: Path = OUT_ANCHORS) -> pd.DataFrame:
    rows = []
    for m, ph_c, cit, ph_a, asc_mg in MATURATION_ANCHORS:
        rows.append(
            {
                "maturity_months": m,
                "pH_citric_curve": ph_c,
                "citric_percent_wv": cit,
                "pH_ascorbic_curve": ph_a,
                "ascorbic_mg_per_100mL": asc_mg,
                "ascorbic_percent_wv": asc_mg / 1000.0,
            }
        )
    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


def generate_dataset(n_samples: int = DEFAULT_N, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """
    Sample maturity uniformly in [4, 12], interpolate both curves, average pH,
    add measurement noise, and attach temperature with a weak secondary effect.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for i in range(n_samples):
        month = float(rng.uniform(4.0, 12.0))

        ph_citric = _interp(month, 0, 1)
        citric = _interp(month, 0, 2)
        ph_asc = _interp(month, 0, 3)
        ascorbic_mg = _interp(month, 0, 4)

        # Consensus pH from both literature curves (+ noise)
        ph = 0.5 * (ph_citric + ph_asc) + float(rng.normal(0.0, 0.04))
        ph = float(np.clip(ph, 4.5, 6.2))

        # Temperature: mild secondary effect (warmer → slightly lower measured acids)
        temperature = float(rng.uniform(18.0, 32.0))
        temp_factor = 1.0 - 0.004 * (temperature - 25.0)

        citric_n = citric * temp_factor + float(rng.normal(0.0, 0.003))
        ascorbic_mg_n = ascorbic_mg * temp_factor + float(rng.normal(0.0, 0.08))
        citric_n = float(np.clip(citric_n, 0.04, 0.16))
        ascorbic_mg_n = float(np.clip(ascorbic_mg_n, 0.7, 3.6))
        ascorbic_pct = ascorbic_mg_n / 1000.0  # % w/v

        rows.append(
            {
                "sample_id": f"MAT{i + 1:04d}",
                "maturity_months": round(month, 2),
                "pH": round(ph, 3),
                "temperature_C": round(temperature, 2),
                "citric_percent_wv": round(citric_n, 5),
                "ascorbic_mg_per_100mL": round(ascorbic_mg_n, 4),
                "ascorbic_percent_wv": round(ascorbic_pct, 6),
                "source": "literature_maturation",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    ML1_DIR.mkdir(parents=True, exist_ok=True)
    anchors = save_anchors()
    df = generate_dataset()

    # ML_1 combined training file
    train = df[["pH", "temperature_C", "citric_percent_wv", "ascorbic_percent_wv"]].copy()
    train.to_csv(OUT_COMBINED, index=False)

    # Keep legacy single-target CSVs in sync for merge_datasets.py
    citric_df = df[["pH", "temperature_C", "citric_percent_wv"]].copy()
    ascorbic_df = df[["pH", "temperature_C", "ascorbic_percent_wv"]].copy()
    citric_df.to_csv(OUT_CITRIC, index=False)
    ascorbic_df.to_csv(OUT_ASCORBIC, index=False)

    print(f"Saved anchors ({len(anchors)} rows) -> {OUT_ANCHORS}")
    print(f"Saved combined training ({len(train)} rows) -> {OUT_COMBINED}")
    print(f"Saved {OUT_CITRIC.name} / {OUT_ASCORBIC.name}")
    print()
    print("Anchor table:")
    print(anchors.to_string(index=False))
    print()
    print(
        f"pH range: {train['pH'].min():.2f}-{train['pH'].max():.2f} | "
        f"citric %: {train['citric_percent_wv'].min():.4f}-{train['citric_percent_wv'].max():.4f} | "
        f"ascorbic %: {train['ascorbic_percent_wv'].min():.6f}-{train['ascorbic_percent_wv'].max():.6f}"
    )


if __name__ == "__main__":
    main()
