"""
Merge citric and ascorbic datasets by nearest (pH, temperature) to create
combined training data: pH, temperature -> citric_percent_wv, ascorbic_percent_wv.

Run from project root: python ML_1/merge_datasets.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CITRIC_PATH = PROJECT_ROOT / "citric_pH_temp_synthetic_600.csv"
ASCORBIC_PATH = PROJECT_ROOT / "ascorbic_pH_temp_synthetic_600.csv"
OUT_PATH = Path(__file__).resolve().parent / "dataset" / "combined_pH_temp_600.csv"


def merge_by_nearest():
    citric = pd.read_csv(CITRIC_PATH)
    ascorbic = pd.read_csv(ASCORBIC_PATH)

    X_citric = citric[["pH", "temperature_C"]].values
    X_ascorbic = ascorbic[["pH", "temperature_C"]].values
    citric_pct = citric["citric_percent_wv"].values
    ascorbic_pct = ascorbic["ascorbic_percent_wv"].values

    # For each citric row, find nearest ascorbic row in (pH, temp) space
    merged_rows = []
    for i in range(len(X_citric)):
        dists = np.sqrt(
            (X_ascorbic[:, 0] - X_citric[i, 0]) ** 2
            + ((X_ascorbic[:, 1] - X_citric[i, 1]) / 10) ** 2  # scale temp
        )
        j = np.argmin(dists)
        merged_rows.append({
            "pH": X_citric[i, 0],
            "temperature_C": X_citric[i, 1],
            "citric_percent_wv": citric_pct[i],
            "ascorbic_percent_wv": ascorbic_pct[j],
        })

    df = pd.DataFrame(merged_rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")
    print(df.head())
    return df


if __name__ == "__main__":
    merge_by_nearest()
