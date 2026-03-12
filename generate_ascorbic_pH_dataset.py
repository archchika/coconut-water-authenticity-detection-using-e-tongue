"""
Generate 600-row synthetic dataset: ascorbic acid (INS 300) concentration vs pH.

- INS 300 = ascorbic acid (vitamin C) food additive; beverage use up to ~3 g/L (0.3% w/v)
- Uses ascorbic acid pKa (~4.17) and electroneutrality (monoprotic approximation)
- Concentration range aligned with INS 300: ~0.0002% to ~0.35% w/v
- Outputs mol/L, g/L, % w/v; includes temperature column

Run: python generate_ascorbic_pH_dataset.py
"""

import numpy as np
import pandas as pd
from math import log10
from scipy.optimize import brentq

# Ascorbic acid pKa (first dissociation) at ~25 °C
pKa_asc = 4.17
Ka_asc = 10 ** (-pKa_asc)

# Water autoprotolysis
Kw = 1e-14  # at 25 °C

# Molar mass of ascorbic acid (g/mol)
MM_ASCORBIC = 176.12


def electroneutrality_ascorbic(H, C):
    """
    Charge balance for monoprotic ascorbic acid (HA <-> H+ + A-).

    H: [H+] in mol/L
    C: total ascorbic acid concentration (Ct) in mol/L
    Returns f(H) = 0 when electroneutrality holds.
    """
    # Fraction of deprotonated form A-: alpha1 = Ka / (Ka + H)
    alpha1 = Ka_asc / (Ka_asc + H)
    charge_anions = C * alpha1  # each A- has charge -1
    return H - Kw / H - charge_anions


def pH_from_ascorbic(C):
    """
    Compute pH for a given total ascorbic acid concentration C (mol/L).
    Uses brentq to solve electroneutrality for H+.
    """
    # Avoid zero concentration
    C = max(C, 1e-8)

    # Search bracket for [H+] between pH 0 and pH 9
    H_min = 1e-9  # pH 9
    H_max = 1.0   # pH 0

    f_min = electroneutrality_ascorbic(H_min, C)
    f_max = electroneutrality_ascorbic(H_max, C)
    if f_min * f_max > 0:
        # Fallback bracket
        H_min, H_max = 1e-10, 1.0
        f_min = electroneutrality_ascorbic(H_min, C)
        f_max = electroneutrality_ascorbic(H_max, C)

    H_root = brentq(electroneutrality_ascorbic, H_min, H_max, args=(C,))
    return -log10(H_root)


def generate_ascorbic_dataset(n_samples=600, seed=42):
    rng = np.random.default_rng(seed)

    # Log-uniform concentrations aligned with INS 300 (ascorbic acid) beverage use:
    # ~1e-5 M to ~0.02 M → ~0.0002% to ~0.35% w/v (covers up to ~3 g/L)
    logC = rng.uniform(-5, -1.7, size=n_samples)
    C = 10 ** logC  # mol/L

    # Add temperature (20–30 °C), matching citric dataset
    temperature = rng.uniform(20.0, 30.0, size=n_samples)

    pH_values = []
    for c in C:
        pH = pH_from_ascorbic(c)
        # Add small measurement noise (e.g. ±0.03 pH units)
        pH_noisy = pH + rng.normal(0.0, 0.03)
        pH_noisy = float(np.clip(pH_noisy, 0.0, 14.0))
        pH_values.append(pH_noisy)

    C = np.asarray(C, dtype=float)
    pH_values = np.asarray(pH_values, dtype=float)

    # Convert to g/L and % w/v (g per 100 mL)
    ascorbic_g_per_L = C * MM_ASCORBIC
    ascorbic_percent_wv = ascorbic_g_per_L / 10.0

    df = pd.DataFrame(
        {
            "pH": pH_values,
            "temperature_C": temperature,
            "ascorbic_conc_M": C,
            "ascorbic_g_per_L": ascorbic_g_per_L,
            "ascorbic_percent_wv": ascorbic_percent_wv,
        }
    )
    return df


if __name__ == "__main__":
    df = generate_ascorbic_dataset(n_samples=600, seed=42)
    out_path = "ascorbic_pH_temp_synthetic_600.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print(df.head())

