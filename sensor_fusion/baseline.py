"""
E-Tongue Sensor Fusion — Baseline normalization (Phase 2.4)
Load baseline (e.g. distilled water) per sensor; subtract from smoothed values.
"""
from __future__ import annotations

from typing import Any

from .input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY

CHANNEL_KEYS = (KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY)

# Config keys for baseline (pipeline.baseline in config.yaml)
BASELINE_CONFIG_KEYS = {
    KEY_PH: "ph",
    KEY_TDS: "tds",
    KEY_TEMPERATURE: "temperature",
    KEY_TURBIDITY: "turbidity",
}


def _get_baselines(pipeline_config: dict[str, Any]) -> dict[str, float]:
    """Extract baseline values from pipeline config; default 0 if missing."""
    bl = pipeline_config.get("baseline") or {}
    return {
        KEY_PH: float(bl.get("ph", 0.0)),
        KEY_TDS: float(bl.get("tds", 0.0)),
        KEY_TEMPERATURE: float(bl.get("temperature", 0.0)),
        KEY_TURBIDITY: float(bl.get("turbidity", 0.0)),
    }


class BaselineNormalizer:
    """
    Subtract baseline (e.g. distilled water reading) per channel.
    normalized_value = value - baseline
    """

    def __init__(self, pipeline_config: dict[str, Any]):
        self._baseline = _get_baselines(pipeline_config)

    def update(self, sample: dict[str, Any]) -> dict[str, Any]:
        """
        Return sample with each channel value replaced by (value - baseline).
        Non-channel keys (timestamp_ms, status) are copied unchanged.
        """
        out: dict[str, Any] = dict(sample)
        for key in CHANNEL_KEYS:
            if key in sample and isinstance(sample[key], (int, float)):
                out[key] = float(sample[key]) - self._baseline[key]
        return out

    def get_baseline(self) -> dict[str, float]:
        """Return current baseline dict (pH, tds, temperature, turbidity)."""
        return dict(self._baseline)
