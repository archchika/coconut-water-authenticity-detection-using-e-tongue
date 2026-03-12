"""
E-Tongue Sensor Fusion — Noise filtering per channel (Phase 2.2)
Low-pass and median filter for pH, TDS, temperature, turbidity; configurable per channel.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from .input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY

CHANNEL_KEYS = (KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY)


class LowPassFilter:
    """Exponential moving average: y_new = alpha * x + (1 - alpha) * y_prev."""

    def __init__(self, alpha: float = 0.3):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = alpha
        self._y: float | None = None

    def update(self, x: float) -> float:
        if self._y is None:
            self._y = x
            return x
        self._y = self.alpha * x + (1.0 - self.alpha) * self._y
        return self._y

    def reset(self) -> None:
        self._y = None


class MedianFilter:
    """Sliding window median: output = median of last `window` inputs."""

    def __init__(self, window: int = 3):
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window
        self._buf: deque[float] = deque(maxlen=window)

    def update(self, x: float) -> float:
        self._buf.append(x)
        sorted_buf = sorted(self._buf)
        n = len(sorted_buf)
        return sorted_buf[n // 2] if n else x

    def reset(self) -> None:
        self._buf.clear()


def _make_filter(filter_config: dict[str, Any], channel_key: str) -> LowPassFilter | MedianFilter:
    """Build one filter from config (type, window, alpha). Prefer channel override, else global."""
    cfg = filter_config.get("channels") or {}
    config_key = channel_key.lower()  # e.g. pH -> ph for config.yaml
    chan_cfg = cfg.get(config_key) or {}
    type_ = (chan_cfg.get("type") or filter_config.get("type") or "median").lower()
    window = int(chan_cfg.get("window") or filter_config.get("window") or 3)
    alpha = float(chan_cfg.get("alpha") or filter_config.get("alpha") or 0.3)
    if type_ == "lowpass":
        return LowPassFilter(alpha=alpha)
    if type_ == "median":
        return MedianFilter(window=window)
    return MedianFilter(window=window)


class PerChannelFilter:
    """
    Apply configurable noise filter per channel (pH, tds, temperature, turbidity).
    Each channel has its own LowPassFilter or MedianFilter instance.
    """

    def __init__(self, pipeline_config: dict[str, Any]):
        filter_config = pipeline_config.get("filter") or {}
        self._filters = {
            KEY_PH: _make_filter(filter_config, KEY_PH),
            KEY_TDS: _make_filter(filter_config, KEY_TDS),
            KEY_TEMPERATURE: _make_filter(filter_config, KEY_TEMPERATURE),
            KEY_TURBIDITY: _make_filter(filter_config, KEY_TURBIDITY),
        }

    def update(self, sample: dict[str, Any]) -> dict[str, Any]:
        """
        Run one raw sample through per-channel filters.
        sample: dict with pH, tds, temperature, turbidity (and optionally timestamp_ms, status).
        Returns new dict with same keys; float channels replaced by filtered values.
        """
        out: dict[str, Any] = dict(sample)
        for key in CHANNEL_KEYS:
            if key in sample and isinstance(sample[key], (int, float)):
                out[key] = self._filters[key].update(float(sample[key]))
        return out

    def reset(self) -> None:
        for f in self._filters.values():
            f.reset()
