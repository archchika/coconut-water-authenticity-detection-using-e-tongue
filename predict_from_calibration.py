"""
Predict citric acid and ascorbic acid % from pH and temperature using calibration curves.
Uses interpolation on the calibration data (citric and ascorbic CSV files).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator

CITRIC_CSV = Path(__file__).parent / "citric_pH_temp_synthetic_600.csv"
ASCORBIC_CSV = Path(__file__).parent / "ascorbic_pH_temp_synthetic_600.csv"

_citric_interp = None
_ascorbic_interp = None


def _load_interpolators():
    global _citric_interp, _ascorbic_interp
    if _citric_interp is not None:
        return

    citric = pd.read_csv(CITRIC_CSV)
    ascorbic = pd.read_csv(ASCORBIC_CSV)

    X_citric = citric[["pH", "temperature_C"]].values
    X_ascorbic = ascorbic[["pH", "temperature_C"]].values
    y_citric = citric["citric_percent_wv"].values
    y_ascorbic = ascorbic["ascorbic_percent_wv"].values

    _citric_interp = LinearNDInterpolator(X_citric, y_citric)
    _ascorbic_interp = LinearNDInterpolator(X_ascorbic, y_ascorbic)


def predict_from_calibration(pH: float, temperature: float) -> dict[str, float]:
    """
    Predict citric and ascorbic acid % from pH and temperature using calibration curves.
    """
    _load_interpolators()
    point = np.array([[pH, temperature]])
    citric = float(_citric_interp(point)[0])
    ascorbic = float(_ascorbic_interp(point)[0])
    # Handle NaN (outside convex hull) with nearest extrapolation
    if np.isnan(citric) or np.isnan(ascorbic):
        citric_df = pd.read_csv(CITRIC_CSV)
        ascorbic_df = pd.read_csv(ASCORBIC_CSV)
        dist_c = np.sqrt((citric_df["pH"] - pH) ** 2 + ((citric_df["temperature_C"] - temperature) / 10) ** 2)
        dist_a = np.sqrt((ascorbic_df["pH"] - pH) ** 2 + ((ascorbic_df["temperature_C"] - temperature) / 10) ** 2)
        citric = citric_df.loc[dist_c.idxmin(), "citric_percent_wv"] if np.isnan(citric) else citric
        ascorbic = ascorbic_df.loc[dist_a.idxmin(), "ascorbic_percent_wv"] if np.isnan(ascorbic) else ascorbic
    return {
        "pH": float(pH),
        "temperature_C": float(temperature),
        "citric_percent_wv": float(citric),
        "ascorbic_percent_wv": float(ascorbic),
    }


def main() -> None:
    if len(sys.argv) >= 3:
        ph = float(sys.argv[1])
        temp = float(sys.argv[2])
    else:
        print("Calibration curve predictor — pH + Temperature → Citric %, Ascorbic %")
        print("-" * 55)
        ph = float(input("Enter pH: "))
        temp = float(input("Enter temperature (°C): "))

    result = predict_from_calibration(ph, temp)
    print()
    print("Output (from calibration curve):")
    print(f"  Citric acid:   {result['citric_percent_wv']:.4f}%")
    print(f"  Ascorbic acid: {result['ascorbic_percent_wv']:.4f}%")


if __name__ == "__main__":
    main()
