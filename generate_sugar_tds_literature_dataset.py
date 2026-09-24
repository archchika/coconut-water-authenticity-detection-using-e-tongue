"""
Generate synthetic E-Tongue calibration CSV from literature Brix–TDS curve (coconut water).

Source: published coconut water study — Brix (%) vs TDS (g/L) over 0–24 h.
Anchor points digitized from the research graph; rows expanded by interpolation + noise.

Outputs:
  - literature_tds_brix_anchor.csv   (6 reference points)
  - literature_tds_sugar_synthetic.csv  (300+ training rows)

CSV schema matches ml/data/calibration/calibration_dataset.csv:
  sample_id, pH, TDS, temperature, turbidity, sugar_pct, citric_acid_pct, ascorbic_acid_pct, notes

Run from project root:
  python generate_sugar_tds_literature_dataset.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ML2_DATASET_DIR = Path(__file__).resolve().parent / "ML_2" / "dataset"

# Digitized anchor points: Time (h), Brix / sugar (%), TDS (g/L)
LITERATURE_ANCHORS = np.array(
    [
        [0, 5.0, 3.2],
        [8, 6.0, 3.1],
        [12, 9.0, 3.3],
        [16, 10.0, 3.8],
        [20, 15.5, 4.5],
        [24, 18.0, 5.8],
    ]
)

ANCHOR_CSV = ML2_DATASET_DIR / "literature_tds_brix_anchor.csv"
OUTPUT_CSV = ML2_DATASET_DIR / "literature_tds_sugar_synthetic.csv"
DEFAULT_N_SAMPLES = 400
DEFAULT_SEED = 42


def save_anchor_points(path: str | Path = ANCHOR_CSV) -> pd.DataFrame:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        LITERATURE_ANCHORS,
        columns=["time_h", "brix_pct", "tds_g_L"],
    )
    df["tds_mg_L"] = df["tds_g_L"] * 1000.0
    df["sugar_pct"] = df["brix_pct"]
    df.to_csv(path, index=False)
    return df


def _interp_at_time(time_h: float) -> tuple[float, float]:
    t = LITERATURE_ANCHORS[:, 0]
    brix = LITERATURE_ANCHORS[:, 1]
    tds = LITERATURE_ANCHORS[:, 2]
    return float(np.interp(time_h, t, brix)), float(np.interp(time_h, t, tds))


def generate_dataset(
    n_samples: int = DEFAULT_N_SAMPLES,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for i in range(n_samples):
        # Spread samples along maturation timeline (0–24 h)
        time_h = float(rng.uniform(0.0, 24.0))
        brix, tds_gL = _interp_at_time(time_h)

        # Sensor / label noise (from graph error-bar scale)
        brix_noisy = brix + rng.normal(0.0, 0.35)
        tds_gL_noisy = tds_gL + rng.normal(0.0, 0.12)
        brix_noisy = float(np.clip(brix_noisy, 4.5, 19.0))
        tds_gL_noisy = float(np.clip(tds_gL_noisy, 2.8, 6.5))

        tds_mgL = tds_gL_noisy * 1000.0

        # sugar_pct = Brix (%)
        sugar_pct = brix_noisy

        # Natural coconut water acids from maturation literature (pH-linked, not random)
        # Digitized curves: higher pH (more mature) → lower citric / ascorbic
        progress = time_h / 24.0
        ph_base = 5.85 - 0.25 * progress
        ph = float(np.clip(ph_base + rng.normal(0.0, 0.06), 5.05, 6.05))

        temperature = float(rng.uniform(16.0, 30.0))
        turbidity = float(np.clip(12.0 + 8.0 * progress + rng.normal(0.0, 4.0), 8.0, 50.0))

        # Map pH onto literature citric / ascorbic maturation envelopes
        # citric % ~ 0.13 at pH 4.75 → 0.06 at pH 5.90
        citric_pct = float(np.interp(ph, [4.75, 5.05, 5.35, 5.62, 5.90], [0.130, 0.110, 0.090, 0.075, 0.060]))
        citric_pct = float(np.clip(citric_pct + rng.normal(0.0, 0.004), 0.04, 0.16))
        # ascorbic mg/100 mL ~ 3.2 at pH 4.78 → 0.95 at pH 5.71 → % w/v = /1000
        ascorbic_mg = float(np.interp(ph, [4.78, 5.10, 5.35, 5.55, 5.71], [3.20, 2.50, 1.85, 1.25, 0.95]))
        ascorbic_mg = float(np.clip(ascorbic_mg + rng.normal(0.0, 0.08), 0.7, 3.6))
        ascorbic_pct = ascorbic_mg / 1000.0

        rows.append(
            {
                "sample_id": f"LIT{i + 1:04d}",
                "pH": round(ph, 2),
                "TDS": round(tds_mgL, 1),
                "temperature": round(temperature, 1),
                "turbidity": round(turbidity, 1),
                "sugar_pct": round(sugar_pct, 4),
                "citric_acid_pct": round(citric_pct, 4),
                "ascorbic_acid_pct": round(ascorbic_pct, 6),
                "notes": f"Literature_Brix_TDS_t{time_h:.1f}h",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    ML2_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    anchors = save_anchor_points()
    df = generate_dataset(n_samples=DEFAULT_N_SAMPLES, seed=DEFAULT_SEED)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"Saved {len(anchors)} anchor points to {ANCHOR_CSV}")
    print(f"Saved {len(df)} synthetic rows to {OUTPUT_CSV}")
    print()
    print("Anchor points (Brix vs TDS):")
    print(anchors.to_string(index=False))
    print()
    print("Synthetic sample (first 5 rows):")
    print(df.head().to_string(index=False))
    print()
    print(
        f"Sugar range: {df['sugar_pct'].min():.2f} – {df['sugar_pct'].max():.2f} %  |  "
        f"TDS range: {df['TDS'].min():.0f} – {df['TDS'].max():.0f} mg/L"
    )


if __name__ == "__main__":
    main()
