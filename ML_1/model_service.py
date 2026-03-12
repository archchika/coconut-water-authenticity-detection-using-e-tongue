"""
Phase 3.4 — Django API: predict_composition(sensor_data) for pH + temperature only.
"""
from typing import Any

try:
    from predict import predict
except ImportError:
    from ML_1.predict import predict


def predict_composition(sensor_data: dict[str, Any]) -> dict[str, float]:
    """
    Input: { "pH": value, "temperature": value }  (or "temperature_C")
    Return: { "citric_acid": predicted_%, "ascorbic_acid": predicted_% }
    """
    ph = float(sensor_data["pH"])
    temp = float(sensor_data.get("temperature") or sensor_data.get("temperature_C", 25.0))
    out = predict(pH=ph, temperature=temp)
    return {
        "citric_acid": out["citric_percent_wv"],
        "ascorbic_acid": out["ascorbic_percent_wv"],
    }


def predict_composition_for_api(sensor_data: dict[str, Any]) -> dict[str, float]:
    """Return full JSON: pH, temperature, citric_percent, ascorbic_percent."""
    ph = float(sensor_data["pH"])
    temp = float(sensor_data.get("temperature") or sensor_data.get("temperature_C", 25.0))
    out = predict(pH=ph, temperature=temp)
    return {
        "pH": round(out["pH"], 2),
        "temperature_C": round(out["temperature_C"], 2),
        "citric_percent": round(out["citric_percent_wv"], 4),
        "ascorbic_percent": round(out["ascorbic_percent_wv"], 4),
    }
