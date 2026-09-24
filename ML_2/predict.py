"""
Prediction: pH, TDS, temperature, turbidity -> sugar_pct.
"""
from pathlib import Path
from typing import Any

import joblib
import numpy as np

_MODEL: Any = None
_MODEL_PATH = Path(__file__).resolve().parent / "models" / "random_forest_sugar_sensors.pkl"


def _get_model() -> Any:
    global _MODEL
    if _MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {_MODEL_PATH}. Run: python ML_2/train_model.py"
            )
        _MODEL = joblib.load(_MODEL_PATH)
    return _MODEL


def predict(
    pH: float,
    tds: float,
    temperature: float,
    turbidity: float,
) -> dict[str, float]:
    """Predict sugar_pct from four sensor readings."""
    model = _get_model()
    X = np.array([[pH, tds, temperature, turbidity]], dtype=np.float64)
    sugar = float(model.predict(X)[0])
    return {
        "pH": float(pH),
        "TDS": float(tds),
        "temperature": float(temperature),
        "turbidity": float(turbidity),
        "sugar_pct": sugar,
    }
