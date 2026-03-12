"""
Generate 600-row synthetic dataset: citric acid (INS 330) concentration vs pH.

- INS 330 = citric acid food additive; range includes lemon/lime juice (~48 g/L, ~5% w/v)
- Uses pKa values and electroneutrality; adds small measurement noise.
- Concentration: ~0.0002% to ~5% w/v (aligned with INS 330 beverage use)

Run: python generate_citric_pH_dataset.py
"""
import numpy as np
import pandas as pd
from math import log10
from scipy.optimize import brentq

# Citric acid pKa values at 25 °C (approx)
pKa1 = 3.13
pKa2 = 4.76
pKa3 = 6.40

Ka1 = 10 ** (-pKa1)
Ka2 = 10 ** (-pKa2)
Ka3 = 10 ** (-pKa3)

# Water autoprotolysis
Kw = 1e-14  # at 25 °C


def electroneutrality(H, C):
    """
    Charge balance for H3A / H2A- / HA2- / A3- citric system.
    H: [H+] in mol/L
    C: total citric acid concentration (Ct) in mol/L
    Returns f(H) = 0 when electroneutrality holds.
    """
    D = H**3 + Ka1 * H**2 + Ka1 * Ka2 * H + Ka1 * Ka2 * Ka3
    alpha1 = Ka1 * H**2 / D
    alpha2 = Ka1 * Ka2 * H / D
    alpha3 = Ka1 * Ka2 * Ka3 / D
    charge_anions = C * (alpha1 + 2 * alpha2 + 3 * alpha3)
    return H - Kw / H - charge_anions


def pH_from_citric(C):
    """Compute pH for total citric acid concentration C (mol/L)."""
    C = max(C, 1e-8)
    H_min = 1e-9
    H_max = 1.0
    f_min = electroneutrality(H_min, C)
    f_max = electroneutrality(H_max, C)
    if f_min * f_max > 0:
        H_min, H_max = 1e-10, 1.0
        f_min = electroneutrality(H_min, C)
        f_max = electroneutrality(H_max, C)
    H_root = brentq(electroneutrality, H_min, H_max, args=(C,))
    return -log10(H_root)


MM_CITRIC = 192.12  # g/mol


def generate_dataset(n_samples=600, seed=42):
    rng = np.random.default_rng(seed)
    # INS 330 range: ~0.0002% to ~5% w/v (covers lemon/lime juice ~48 g/L)
    logC = rng.uniform(-5, -0.58, size=n_samples)
    C = 10 ** logC
    pH_values = []
    for c in C:
        pH = pH_from_citric(c)
        pH_noisy = pH + rng.normal(0.0, 0.03)
        pH_noisy = float(np.clip(pH_noisy, 0.0, 14.0))
        pH_values.append(pH_noisy)

    # Add temperature (20–30 °C)
    temperature = rng.uniform(20.0, 30.0, size=n_samples)

    # Citric acid in g/L and % w/v
    citric_g_per_L = C * MM_CITRIC
    citric_percent_wv = citric_g_per_L / 10.0  # g per 100 mL

    df = pd.DataFrame({
        "pH": np.array(pH_values),
        "temperature_C": temperature,
        "citric_conc_M": C,
        "citric_g_per_L": citric_g_per_L,
        "citric_percent_wv": citric_percent_wv,
    })
    return df


if __name__ == "__main__":
    df = generate_dataset(n_samples=600, seed=42)
    out_path = "citric_pH_temp_synthetic_600.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print(df.head())
