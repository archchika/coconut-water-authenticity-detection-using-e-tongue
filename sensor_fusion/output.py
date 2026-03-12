"""
E-Tongue Sensor Fusion — Structured output and API (Phase 2.6)
JSON/dict with timestamp ISO8601; log raw and fused for debug.
get_feature_vector() for Phase 3 lives in features.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from .config_loader import get_log_config
from .input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY

logger = logging.getLogger(__name__)

# API output uses "temp" (deliverable spec); internal uses "temperature"
KEY_TEMP_OUT = "temp"


def timestamp_ms_to_iso8601(ms: int | None) -> str:
    """Convert timestamp_ms (from ESP32) to ISO8601 UTC string."""
    if ms is None:
        return ""
    try:
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except (ValueError, OSError):
        return ""


def to_structured_output(sample: dict[str, Any]) -> dict[str, Any]:
    """
    Build structured dict for ML/API: pH, tds, temp, turbidity, timestamp (ISO8601), status.
    """
    ms = sample.get("timestamp_ms")
    return {
        "pH": float(sample.get(KEY_PH, 0)),
        "tds": float(sample.get(KEY_TDS, 0)),
        KEY_TEMP_OUT: float(sample.get(KEY_TEMPERATURE, 0)),
        "turbidity": float(sample.get(KEY_TURBIDITY, 0)),
        "timestamp": timestamp_ms_to_iso8601(ms) or None,
        "status": sample.get("status", "unknown"),
    }


def log_raw(config: dict[str, Any], sample: dict[str, Any]) -> None:
    """If config.log.raw is true, log the raw sample for debug."""
    log_cfg = get_log_config(config)
    if log_cfg.get("raw"):
        logger.debug("raw sample: %s", sample)


def log_fused(config: dict[str, Any], structured: dict[str, Any]) -> None:
    """If config.log.fused is true, log the fused structured output for debug."""
    log_cfg = get_log_config(config)
    if log_cfg.get("fused"):
        logger.debug("fused output: %s", structured)
