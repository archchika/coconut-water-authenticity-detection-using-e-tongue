"""
Django / API helper: predict sugar from sensor_data dict.
"""
from typing import Any

try:
    from predict import predict
except ImportError:
    from ML_2.predict import predict


def predict_sugar(sensor_data: dict[str, Any]) -> dict[str, float]:
    """
    Input: { "pH", "tds" or "TDS", "temperature", "turbidity" }
    Return: { "sugar": predicted sugar % }
    """
    ph = float(sensor_data["pH"])
    tds = float(sensor_data.get("tds") or sensor_data.get("TDS"))
    temp = float(sensor_data.get("temperature") or sensor_data.get("temperature_C", 25.0))
    turb = float(sensor_data.get("turbidity") or sensor_data.get("Turbidity", 0.0))
    out = predict(pH=ph, tds=tds, temperature=temp, turbidity=turb)
    return {"sugar": out["sugar_pct"]}


def predict_sugar_for_api(sensor_data: dict[str, Any]) -> dict[str, float]:
    """Return rounded JSON-friendly fields."""
    ph = float(sensor_data["pH"])
    tds = float(sensor_data.get("tds") or sensor_data.get("TDS"))
    temp = float(sensor_data.get("temperature") or sensor_data.get("temperature_C", 25.0))
    turb = float(sensor_data.get("turbidity") or sensor_data.get("Turbidity", 0.0))
    out = predict(pH=ph, tds=tds, temperature=temp, turbidity=turb)
    return {
        "pH": round(out["pH"], 2),
        "TDS": round(out["TDS"], 1),
        "temperature": round(out["temperature"], 1),
        "turbidity": round(out["turbidity"], 1),
        "sugar_percent": round(out["sugar_pct"], 4),
    }
