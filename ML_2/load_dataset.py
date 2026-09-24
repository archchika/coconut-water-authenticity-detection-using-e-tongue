"""
Load combined dataset: pH, TDS, temperature, turbidity -> sugar_pct.
"""
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["pH", "TDS", "temperature", "turbidity"]
TARGET_COLUMN = "sugar_pct"


def get_dataset_path() -> Path:
    return Path(__file__).resolve().parent / "dataset" / "combined_sensors_sugar.csv"


def load_dataset(csv_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else get_dataset_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Run: python ML_2/merge_datasets.py"
        )
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def prepare_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    for col in FEATURE_COLUMNS + [TARGET_COLUMN]:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
    df_clean = df[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna()
    X = df_clean[FEATURE_COLUMNS].astype(np.float64).values
    y = df_clean[TARGET_COLUMN].astype(np.float64).values
    return X, y


def load_xy(csv_path: str | Path | None = None) -> Tuple[np.ndarray, np.ndarray]:
    df = load_dataset(csv_path)
    return prepare_xy(df)
