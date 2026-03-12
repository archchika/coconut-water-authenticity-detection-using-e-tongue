"""
E-Tongue Sensor Fusion — Feature vector assembly (Phase 2.5)
Build single array per sample: [pH, TDS, temperature, turbidity]; optional derived features.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY
from .output import timestamp_ms_to_iso8601

# Fixed order for ML (Phase 3); must match training feature order
FEATURE_ORDER = [KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY]

# Optional derived feature names (computed if listed in pipeline.derived_features)
DERIVED = {
    "ph_tds": lambda ph, tds, temp, turb: ph * (tds / 1000.0),  # scale-down for magnitude
    "turb_per_temp": lambda ph, tds, temp, turb: turb / max(float(temp), 0.1),  # avoid div by zero
    "tds_per_ph": lambda ph, tds, temp, turb: tds / max(abs(float(ph)), 0.1),
}


def sample_to_array(
    sample: dict[str, Any],
    *,
    include_derived: list[str] | None = None,
) -> np.ndarray:
    """
    Build feature array from sample dict.
    Base: [pH, tds, temperature, turbidity]. If include_derived is given, append those in order.
    """
    base = [float(sample[k]) for k in FEATURE_ORDER if k in sample]
    if len(base) != 4:
        raise KeyError(f"Sample must contain {FEATURE_ORDER}; got keys {list(sample.keys())}")
    ph, tds, temp, turb = base
    out: list[float] = list(base)
    if include_derived:
        for name in include_derived:
            if name in DERIVED:
                out.append(float(DERIVED[name](ph, tds, temp, turb)))
    return np.array(out, dtype=np.float64)


def get_feature_vector(
    sample: dict[str, Any],
    pipeline_config: dict[str, Any] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Build feature vector for Phase 3 ML input.
    Returns (feature_array, metadata). metadata has timestamp_ms, status, and optional timestamp (ISO8601).
    """
    derived = []
    if pipeline_config:
        derived = list(pipeline_config.get("derived_features") or [])
    arr = sample_to_array(sample, include_derived=derived if derived else None)
    metadata: dict[str, Any] = {
        "timestamp_ms": sample.get("timestamp_ms"),
        "timestamp": timestamp_ms_to_iso8601(sample.get("timestamp_ms")),
        "status": sample.get("status", "unknown"),
    }
    return arr, metadata


def feature_names(pipeline_config: dict[str, Any] | None = None) -> list[str]:
    """Return list of feature names in same order as get_feature_vector array (for ML/plots)."""
    names = list(FEATURE_ORDER)
    if pipeline_config:
        for d in pipeline_config.get("derived_features") or []:
            if d in DERIVED:
                names.append(d)
    return names
