"""
Local dashboard — Load config (Phase 4.1)
"""
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load config from YAML. Returns dict; raises if file missing or invalid."""
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


def get_data_source_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return data_source section (url, refresh_interval_sec, timeout_sec)."""
    return config.get("data_source") or {}


def get_graphs_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return graphs section (max_points, max_seconds) for Phase 4.2."""
    return config.get("graphs") or {}
