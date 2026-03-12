"""
E-Tongue Sensor Fusion — Moving average smoothing (Phase 2.3)
Rolling window per sensor; output smoothed stream.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from .input_sources import KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY

CHANNEL_KEYS = (KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY)


class RollingMovingAverage:
    """Rolling window mean: output = mean of last `window` inputs."""

    def __init__(self, window: int = 5):
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window
        self._buf: deque[float] = deque(maxlen=window)

    def update(self, x: float) -> float:
        self._buf.append(x)
        return sum(self._buf) / len(self._buf)

    def reset(self) -> None:
        self._buf.clear()


def _window_for_channel(pipeline_config: dict[str, Any], channel_key: str) -> int:
    """Get moving average window for channel; prefer per-channel, else global."""
    windows = pipeline_config.get("moving_average_windows") or {}
    config_key = channel_key.lower()
    if config_key in windows:
        return int(windows[config_key])
    return int(pipeline_config.get("moving_average_window") or 5)


class PerChannelMovingAverage:
    """
    Rolling moving average per channel (pH, tds, temperature, turbidity).
    Each channel has its own window (from config); output smoothed sample dict.
    """

    def __init__(self, pipeline_config: dict[str, Any]):
        self._smoothers = {
            KEY_PH: RollingMovingAverage(_window_for_channel(pipeline_config, KEY_PH)),
            KEY_TDS: RollingMovingAverage(_window_for_channel(pipeline_config, KEY_TDS)),
            KEY_TEMPERATURE: RollingMovingAverage(
                _window_for_channel(pipeline_config, KEY_TEMPERATURE)
            ),
            KEY_TURBIDITY: RollingMovingAverage(
                _window_for_channel(pipeline_config, KEY_TURBIDITY)
            ),
        }

    def update(self, sample: dict[str, Any]) -> dict[str, Any]:
        """
        Run one sample through per-channel rolling mean.
        sample: dict with pH, tds, temperature, turbidity (and optionally timestamp_ms, status).
        Returns new dict with same keys; float channels replaced by smoothed values.
        """
        out: dict[str, Any] = dict(sample)
        for key in CHANNEL_KEYS:
            if key in sample and isinstance(sample[key], (int, float)):
                out[key] = self._smoothers[key].update(float(sample[key]))
        return out

    def reset(self) -> None:
        for s in self._smoothers.values():
            s.reset()
