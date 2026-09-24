"""
Compute E-Tongue sensor accuracy vs laboratory reference readings.

Usage:
  1. Fill in docs/research/sensor_lab_comparison_template.csv with lab + sensor values.
  2. Run: python compute_sensor_lab_accuracy.py
  3. Results saved to docs/research/sensor_lab_accuracy_results.json
     and printed as a thesis-ready table.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "docs" / "research" / "sensor_lab_comparison_template.csv"
OUTPUT_JSON = ROOT / "docs" / "research" / "sensor_lab_accuracy_results.json"


def mape(actual: list[float], predicted: list[float]) -> float:
    errors = []
    for a, p in zip(actual, predicted):
        if a == 0:
            errors.append(abs(p) * 100)
        else:
            errors.append(abs(p - a) / abs(a) * 100)
    return float(np.mean(errors)) if errors else 0.0


def ph_accuracy_pct(lab: list[float], sensor: list[float]) -> dict[str, float]:
    """Match june30_validation.py: accuracy from MAE scaled to pH 0-14 range."""
    mae = float(np.mean([abs(a - p) for a, p in zip(lab, sensor)]))
    accuracy = max(0.0, 100.0 - mae / 6.0 * 100)
    return {"mae": round(mae, 4), "accuracy_pct": round(accuracy, 2)}


def sensor_accuracy_pct(lab: list[float], sensor: list[float]) -> dict[str, float]:
    """MAPE-based accuracy used for sugar/citric/ascorbic in validation."""
    m = mape(lab, sensor)
    return {"mape_pct": round(m, 2), "accuracy_pct": round(max(0.0, 100.0 - m), 2)}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_pairs(rows: list[dict[str, str]], lab_key: str, sensor_key: str) -> tuple[list[float], list[float]]:
    lab_vals: list[float] = []
    sensor_vals: list[float] = []
    for row in rows:
        lab_raw = (row.get(lab_key) or "").strip()
        sensor_raw = (row.get(sensor_key) or "").strip()
        if not lab_raw or not sensor_raw:
            continue
        lab_vals.append(float(lab_raw))
        sensor_vals.append(float(sensor_raw))
    return lab_vals, sensor_vals


def compute_all(rows: list[dict[str, str]]) -> dict:
    sensors = {
        "ph": ("lab_ph", "sensor_ph", ph_accuracy_pct),
        "tds_ppm": ("lab_tds_ppm", "sensor_tds_ppm", sensor_accuracy_pct),
        "turbidity_ntu": ("lab_turbidity_ntu", "sensor_turbidity_ntu", sensor_accuracy_pct),
        "temperature_c": ("lab_temperature_c", "sensor_temperature_c", sensor_accuracy_pct),
    }

    per_sensor: dict[str, dict] = {}
    for name, (lab_key, sensor_key, fn) in sensors.items():
        lab, sensor = parse_pairs(rows, lab_key, sensor_key)
        if not lab:
            per_sensor[name] = {
                "sample_count": 0,
                "accuracy_pct": None,
                "note": "No paired lab/sensor values found in CSV",
            }
            continue
        metrics = fn(lab, sensor)
        per_sensor[name] = {"sample_count": len(lab), **metrics}

    completed = [s["accuracy_pct"] for s in per_sensor.values() if s.get("accuracy_pct") is not None]
    overall = round(float(np.mean(completed)), 2) if completed else None

    return {
        "total_rows": len(rows),
        "sensors": per_sensor,
        "overall_sensor_accuracy_pct": overall,
    }


def print_table(results: dict) -> None:
    print("\n=== E-Tongue Sensor Accuracy vs Laboratory ===\n")
    print(f"{'Sensor':<18} {'Samples':>8} {'Accuracy %':>12}")
    print("-" * 40)
    labels = {
        "ph": "pH",
        "tds_ppm": "TDS (ppm)",
        "turbidity_ntu": "Turbidity (NTU)",
        "temperature_c": "Temperature (°C)",
    }
    for key, label in labels.items():
        s = results["sensors"][key]
        n = s.get("sample_count", 0)
        acc = s.get("accuracy_pct")
        acc_str = f"{acc:.2f}" if acc is not None else "— (fill CSV)"
        print(f"{label:<18} {n:>8} {acc_str:>12}")
    print("-" * 40)
    overall = results.get("overall_sensor_accuracy_pct")
    overall_str = f"{overall:.2f}" if overall is not None else "—"
    print(f"{'Overall (mean)':<18} {'':<8} {overall_str:>12}")
    print()


def main() -> None:
    csv_path = DEFAULT_CSV
    if not csv_path.is_file():
        raise FileNotFoundError(f"Template not found: {csv_path}")

    rows = load_rows(csv_path)
    results = compute_all(rows)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print_table(results)
    print(f"Saved: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
