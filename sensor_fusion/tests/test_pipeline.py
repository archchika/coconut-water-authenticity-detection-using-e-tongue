"""
Unit tests and validation for sensor_fusion pipeline (Phase 2.7).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure project root (research/) is on path when running tests from repo
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from sensor_fusion import (
    load_config,
    FusionPipeline,
    get_feature_vector,
    to_structured_output,
)
from sensor_fusion.config_loader import get_pipeline_config

# Sample data for validation (ESP32-like JSON parsed to dict)
SAMPLE_RAW = {
    "timestamp_ms": 1000,
    "pH": 5.4,
    "tds": 120.0,
    "temperature": 25.0,
    "turbidity": 80.0,
    "status": "unknown",
}

MORE_SAMPLES = [
    {"timestamp_ms": 2000, "pH": 5.3, "tds": 115.0, "temperature": 24.5, "turbidity": 75.0, "status": "ok"},
    {"timestamp_ms": 3000, "pH": 5.5, "tds": 125.0, "temperature": 25.2, "turbidity": 85.0, "status": "ok"},
]


@pytest.fixture
def config():
    """Load config from package config.yaml."""
    return load_config(Path(__file__).resolve().parent.parent / "config.yaml")


@pytest.fixture
def pipeline(config):
    return FusionPipeline(config)


def test_pipeline_single_sample(pipeline):
    """Full pipeline on one raw sample returns structured output and feature array."""
    structured, arr, meta = pipeline.update(SAMPLE_RAW.copy())
    assert "pH" in structured and "tds" in structured and "temp" in structured and "turbidity" in structured
    assert "timestamp" in structured and "status" in structured
    assert isinstance(structured["pH"], (int, float))
    assert len(arr) == 4  # base features only by default
    assert arr.dtype == np.float64
    assert "timestamp_ms" in meta and "status" in meta and "timestamp" in meta


def test_pipeline_multiple_samples(pipeline):
    """Pipeline with multiple samples (moving average fills, filter settles)."""
    for s in MORE_SAMPLES:
        structured, arr, meta = pipeline.update(s)
        assert len(arr) == 4
        assert structured["status"] in ("ok", "unknown")


def test_feature_vector_order(config):
    """Feature array order matches FEATURE_ORDER (pH, tds, temperature, turbidity)."""
    pipe_cfg = get_pipeline_config(config)
    _, arr, _ = get_feature_vector(SAMPLE_RAW, pipe_cfg)
    assert list(arr) == [SAMPLE_RAW["pH"], SAMPLE_RAW["tds"], SAMPLE_RAW["temperature"], SAMPLE_RAW["turbidity"]]


def test_structured_output_keys():
    """to_structured_output has required keys for ML/API."""
    out = to_structured_output(SAMPLE_RAW)
    assert set(out.keys()) >= {"pH", "tds", "temp", "turbidity", "timestamp", "status"}
    assert out["temp"] == SAMPLE_RAW["temperature"]


def test_pipeline_reset(pipeline):
    """Reset clears state; next update still returns valid output."""
    pipeline.update(SAMPLE_RAW.copy())
    pipeline.reset()
    structured, arr, _ = pipeline.update(SAMPLE_RAW.copy())
    assert len(arr) == 4
    assert "pH" in structured
