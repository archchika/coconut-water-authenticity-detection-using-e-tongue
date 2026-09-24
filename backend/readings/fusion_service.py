"""
Sensor fusion for ML path: filter + moving average (raw-scale values for ML_1/ML_2).
"""
from __future__ import annotations

from typing import Any

from sensor_fusion.config_loader import load_config
from sensor_fusion.pipeline import FusionPipeline
from sensor_fusion.input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY


def _pick_numeric(data: dict[str, Any], *keys: str) -> float:
    """Read first present key; do not treat 0 as missing (avoid `or` chains)."""
    for key in keys:
        if key in data and data[key] is not None:
            return float(data[key])
    raise KeyError(f"Missing numeric field; tried keys: {keys}")


def _raw_to_sample(data: dict[str, Any]) -> dict[str, Any]:
    ph = _pick_numeric(data, "pH", "ph")
    tds = _pick_numeric(data, "tds", "TDS")
    temp = _pick_numeric(data, "temperature", "temperature_C")
    turb = _pick_numeric(data, "turbidity", "Turbidity")
    return {
        KEY_PH: ph,
        KEY_TDS: tds,
        KEY_TEMPERATURE: temp,
        KEY_TURBIDITY: turb,
        "timestamp_ms": data.get("timestamp_ms"),
        "status": data.get("status", "unknown"),
    }


def fuse_samples_for_ml(raw_readings: list[dict[str, Any]]) -> list[dict[str, float]]:
    """
    Run each raw sample through filter + moving average (no baseline subtract — ML trained on raw scale).
    Returns list of fused sensor dicts in order.
    """
    config = load_config()
    pipeline = FusionPipeline(config)
    fused: list[dict[str, float]] = []
    for raw in raw_readings:
        sample = _raw_to_sample(raw)
        filtered = pipeline._filter.update(sample)
        smoothed = pipeline._smoother.update(filtered)
        fused.append(
            {
                "pH": float(smoothed[KEY_PH]),
                "tds": float(smoothed[KEY_TDS]),
                "temperature": float(smoothed[KEY_TEMPERATURE]),
                "turbidity": float(smoothed[KEY_TURBIDITY]),
            }
        )
    return fused
