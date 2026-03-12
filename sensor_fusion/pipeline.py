"""
E-Tongue Sensor Fusion — Pipeline integration (Phase 2.7)
Wire: Raw → Filter → Moving avg → Baseline → Feature vector / Structured output.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .config_loader import get_pipeline_config
from .filters import PerChannelFilter
from .smoothing import PerChannelMovingAverage
from .baseline import BaselineNormalizer
from .features import get_feature_vector
from .output import to_structured_output, log_raw, log_fused


class FusionPipeline:
    """
    Full pipeline: raw sample → filter → moving average → baseline → structured output + feature vector.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        pipe = get_pipeline_config(config)
        self._filter = PerChannelFilter(pipe)
        self._smoother = PerChannelMovingAverage(pipe)
        self._baseline = BaselineNormalizer(pipe)

    def update(self, raw_sample: dict[str, Any]) -> tuple[dict[str, Any], np.ndarray, dict[str, Any]]:
        """
        Run one raw sample through the pipeline.
        Returns (structured_output, feature_array, metadata).
        - structured_output: dict with pH, tds, temp, turbidity, timestamp (ISO8601), status
        - feature_array: 1D numpy array for Phase 3 ML
        - metadata: timestamp_ms, timestamp, status
        """
        log_raw(self.config, raw_sample)
        filtered = self._filter.update(raw_sample)
        smoothed = self._smoother.update(filtered)
        normalized = self._baseline.update(smoothed)
        structured = to_structured_output(normalized)
        arr, metadata = get_feature_vector(normalized, get_pipeline_config(self.config))
        log_fused(self.config, structured)
        return structured, arr, metadata

    def reset(self) -> None:
        """Reset filter, smoother state (e.g. for new run)."""
        self._filter.reset()
        self._smoother.reset()
