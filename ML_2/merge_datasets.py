"""
Merge literature Brix–TDS synthetic data + ml calibration CSV into one training file.

Sources:
  - ML_2/dataset/literature_tds_sugar_synthetic.csv  (from generate_sugar_tds_literature_dataset.py)
  - ml/data/calibration/calibration_dataset.csv      (existing natural + artificial samples)

Output:
  - ML_2/dataset/combined_sensors_sugar.csv

Run from project root: python ML_2/merge_datasets.py
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LITERATURE_PATH = Path(__file__).resolve().parent / "dataset" / "literature_tds_sugar_synthetic.csv"
CALIBRATION_PATH = PROJECT_ROOT / "ml" / "data" / "calibration" / "calibration_dataset.csv"
OUT_PATH = Path(__file__).resolve().parent / "dataset" / "combined_sensors_sugar.csv"

CANONICAL_COLUMNS = [
    "sample_id",
    "pH",
    "TDS",
    "temperature",
    "turbidity",
    "sugar_pct",
    "citric_acid_pct",
    "ascorbic_acid_pct",
    "source",
    "notes",
]


def _normalize(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    rename = {}
    if "temperature_C" in df.columns and "temperature" not in df.columns:
        rename["temperature_C"] = "temperature"
    df = df.rename(columns=rename)

    for col in ["pH", "TDS", "temperature", "turbidity", "sugar_pct"]:
        if col not in df.columns:
            raise ValueError(f"{source}: missing column {col}")

    if "citric_acid_pct" not in df.columns:
        df["citric_acid_pct"] = 0.0
    if "ascorbic_acid_pct" not in df.columns:
        df["ascorbic_acid_pct"] = 0.0
    if "sample_id" not in df.columns:
        df["sample_id"] = [f"{source[:3].upper()}{i:04d}" for i in range(len(df))]
    if "notes" not in df.columns:
        df["notes"] = ""

    df["source"] = source
    return df[CANONICAL_COLUMNS]


def merge_all() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    if LITERATURE_PATH.exists():
        lit = pd.read_csv(LITERATURE_PATH)
        frames.append(_normalize(lit, "literature"))
    else:
        print(f"Warning: {LITERATURE_PATH} not found. Run generate_sugar_tds_literature_dataset.py first.")

    if CALIBRATION_PATH.exists():
        cal = pd.read_csv(CALIBRATION_PATH)
        frames.append(_normalize(cal, "calibration"))
    else:
        print(f"Warning: {CALIBRATION_PATH} not found.")

    if not frames:
        raise FileNotFoundError("No input datasets found.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["pH", "TDS", "temperature", "turbidity", "sugar_pct"],
        keep="first",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(combined)} rows to {OUT_PATH}")
    print(f"  literature: {(combined['source'] == 'literature').sum()}")
    print(f"  calibration: {(combined['source'] == 'calibration').sum()}")
    print(combined[["pH", "TDS", "sugar_pct", "source"]].head())
    return combined


if __name__ == "__main__":
    merge_all()
