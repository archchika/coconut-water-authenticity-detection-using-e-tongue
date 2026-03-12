"""
E-Tongue Sensor Fusion — Config loader (Phase 2.1)
Load config.yaml and expose pipeline and input settings.
"""
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# Default config path relative to this package
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load config from YAML file. Returns dict; raises if file missing or invalid."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML object (dict).")
    return data


def get_input_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return input section (source type and params)."""
    return config.get("input") or {}


def get_pipeline_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return pipeline section (moving_average_window, baseline, filter)."""
    return config.get("pipeline") or {}


def get_log_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return log section (raw, fused)."""
    return config.get("log") or {}
