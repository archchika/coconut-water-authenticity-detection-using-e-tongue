"""
Local dashboard — Fetch data from ESP32 / local ML server (Phase 4.1)
Poll HTTP endpoint for latest reading.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def fetch_latest_reading(
    url: str,
    timeout_sec: float = 5.0,
) -> dict[str, Any] | None:
    """
    GET url and parse JSON as latest reading.
    Expected keys: timestamp_ms, pH, tds, temperature, turbidity, status.
    Optional: predicted_sugar, predicted_citric, predicted_ascorbic, authenticity.
    Returns None on failure or invalid response.
    """
    try:
        import requests
    except ImportError:
        logger.warning("requests not installed; pip install requests")
        return None
    try:
        r = requests.get(url, timeout=timeout_sec)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            return None
        # Require at least sensor keys
        required = ("pH", "tds", "temperature", "turbidity")
        if not all(k in data for k in required):
            logger.debug("Response missing required keys: %s", list(data.keys()))
            return None
        return data
    except Exception as e:
        logger.debug("fetch_latest_reading failed: %s", e)
        return None
