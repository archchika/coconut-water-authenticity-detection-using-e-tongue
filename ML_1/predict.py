"""
Phase 3.3 — Prediction: pH, temperature -> citric_percent_wv, ascorbic_percent_wv.
"""
from pathlib import Path
from typing import Any

import joblib
import numpy as np

_MODEL: Any = None
_MODEL_PATH = Path(__file__).resolve().parent / "models" / "random_forest_ph_temp.pkl"


def _get_model() -> Any:
    global _MODEL
    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {_MODEL_PATH}. Run: python ML_1/train_model.py"
            )
        _MODEL = joblib.load(_MODEL_PATH)
    return _MODEL


def predict(pH: float, temperature: float) -> dict[str, float]:
    """Predict citric_percent_wv and ascorbic_percent_wv from pH and temperature."""
    model = _get_model()
    X = np.array([[pH, temperature]], dtype=np.float64)
    y_pred = model.predict(X)[0]
    return {
        "pH": float(pH),
        "temperature_C": float(temperature),
        "citric_percent_wv": float(y_pred[0]),
        "ascorbic_percent_wv": float(y_pred[1]),
    }
