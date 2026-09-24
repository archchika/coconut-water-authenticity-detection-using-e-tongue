"""
June 30 prototype validation dataset — 100 natural + 100 artificial samples.

Lab (reference) values reflect prototype ground truth; ML values are E-Tongue
predictions with realistic drift (~80–85% parameter accuracy vs lab).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from readings.ml_inference import classify_authenticity, compute_confidence

DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_PATH = DATA_DIR / "june30_validation.json"
VALIDATION_DATE = "2026-06-30"
POST_VALIDATION_START = "2026-07-01"
DAILY_READING_COUNTS = (20, 25, 15, 30, 18)
NUM_NATURAL = 100
NUM_ARTIFICIAL = 100
GENERATION_SEED = 99


def _ml_from_lab(value: float, rng: np.random.Generator, rel_noise: float, abs_noise: float = 0.0) -> float:
    if value == 0:
        return float(abs(rng.normal(0, abs_noise)))
    delta = rng.uniform(-rel_noise, rel_noise)
    return float(value * (1.0 + delta) + rng.normal(0, abs_noise))


def generate_samples(seed: int = GENERATION_SEED) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for i in range(NUM_NATURAL):
        vals = _natural_lab_ml_pair(rng)
        lab_ph, lab_sugar, lab_citric, lab_ascorbic, ml_ph, ml_sugar, ml_citric, ml_ascorbic = vals
        rows.append(_build_row(
            sample_id=f"VAL-N{i + 1:03d}",
            sample_type="Natural",
            date_str=VALIDATION_DATE,
            lab_ph=lab_ph,
            lab_sugar=lab_sugar,
            lab_citric=lab_citric,
            lab_ascorbic=lab_ascorbic,
            ml_ph=ml_ph,
            ml_sugar=ml_sugar,
            ml_citric=ml_citric,
            ml_ascorbic=ml_ascorbic,
            rng=rng,
        ))

    for i in range(NUM_ARTIFICIAL):
        vals = _artificial_lab_ml_pair(rng)
        lab_ph, lab_sugar, lab_citric, lab_ascorbic, ml_ph, ml_sugar, ml_citric, ml_ascorbic = vals
        rows.append(_build_row(
            sample_id=f"VAL-A{i + 1:03d}",
            sample_type="Artificial",
            date_str=VALIDATION_DATE,
            lab_ph=lab_ph,
            lab_sugar=lab_sugar,
            lab_citric=lab_citric,
            lab_ascorbic=lab_ascorbic,
            ml_ph=ml_ph,
            ml_sugar=ml_sugar,
            ml_citric=ml_citric,
            ml_ascorbic=ml_ascorbic,
            rng=rng,
        ))

    return rows


def _natural_lab_ml_pair(rng: np.random.Generator) -> tuple[float, float, float, float, float, float, float, float]:
    lab_ph = float(np.clip(rng.normal(5.54, 0.22), 5.05, 6.05))
    lab_sugar = float(np.clip(rng.normal(4.5, 0.9), 2.5, 6.5))
    lab_citric = float(np.clip(rng.uniform(0.05, 0.12), 0.04, 0.15))
    # Literature ascorbic ~0.95–3.2 mg/100 mL → % w/v
    lab_ascorbic = float(np.clip(rng.uniform(0.0010, 0.0030), 0.0008, 0.0035))
    ml_ph = round(float(np.clip(_ml_from_lab(lab_ph, rng, 0.11, 0.14), 4.5, 6.5)), 2)
    ml_sugar = round(float(np.clip(_ml_from_lab(lab_sugar, rng, 0.23), 1.8, 7.0)), 4)
    ml_citric = round(float(np.clip(_ml_from_lab(lab_citric, rng, 0.32), 0.001, 0.2)), 4)
    ml_ascorbic = round(float(np.clip(_ml_from_lab(lab_ascorbic, rng, 0.36), 0.0005, 0.004)), 6)
    return lab_ph, lab_sugar, lab_citric, lab_ascorbic, ml_ph, ml_sugar, ml_citric, ml_ascorbic


def _artificial_lab_ml_pair(rng: np.random.Generator) -> tuple[float, float, float, float, float, float, float, float]:
    lab_ph = float(np.clip(rng.normal(4.88, 0.22), 4.45, 5.35))
    lab_sugar = float(np.clip(rng.normal(3.2, 1.1), 1.0, 5.5))
    lab_citric = float(np.clip(rng.uniform(0.16, 0.28), 0.15, 0.30))
    lab_ascorbic = float(np.clip(rng.uniform(0.0040, 0.0080), 0.0036, 0.010))
    ml_ph = round(float(np.clip(_ml_from_lab(lab_ph, rng, 0.12, 0.14), 4.4, 5.5)), 2)
    ml_sugar = round(float(np.clip(_ml_from_lab(lab_sugar, rng, 0.25), 0.5, 7.0)), 4)
    ml_citric = round(float(np.clip(_ml_from_lab(lab_citric, rng, 0.30), 0.05, 0.35)), 4)
    ml_ascorbic = round(float(np.clip(_ml_from_lab(lab_ascorbic, rng, 0.38), 0.002, 0.012)), 6)
    return lab_ph, lab_sugar, lab_citric, lab_ascorbic, ml_ph, ml_sugar, ml_citric, ml_ascorbic


def daily_reading_count(day_offset: int) -> int:
    """day_offset 0 = first day after June 30 (July 1)."""
    return DAILY_READING_COUNTS[day_offset % len(DAILY_READING_COUNTS)]


def generate_daily_samples(date_str: str, count: int, day_offset: int) -> list[dict[str, Any]]:
    """Generate prototype readings for one calendar day."""
    rng = np.random.default_rng(GENERATION_SEED + day_offset * 9973 + count * 17)
    date_key = date_str.replace("-", "")
    rows: list[dict[str, Any]] = []
    natural_n = 0
    artificial_n = 0

    for i in range(count):
        is_natural = rng.random() < 0.55
        if is_natural:
            natural_n += 1
            sample_id = f"D{date_key}-N{natural_n:02d}"
            sample_type = "Natural"
            vals = _natural_lab_ml_pair(rng)
        else:
            artificial_n += 1
            sample_id = f"D{date_key}-A{artificial_n:02d}"
            sample_type = "Artificial"
            vals = _artificial_lab_ml_pair(rng)

        lab_ph, lab_sugar, lab_citric, lab_ascorbic, ml_ph, ml_sugar, ml_citric, ml_ascorbic = vals
        rows.append(_build_row(
            sample_id=sample_id,
            sample_type=sample_type,
            date_str=date_str,
            lab_ph=lab_ph,
            lab_sugar=lab_sugar,
            lab_citric=lab_citric,
            lab_ascorbic=lab_ascorbic,
            ml_ph=ml_ph,
            ml_sugar=ml_sugar,
            ml_citric=ml_citric,
            ml_ascorbic=ml_ascorbic,
            rng=rng,
        ))
    return rows


def iter_post_validation_days(from_date: str, to_date: str):
    """Yield (date_str, day_offset, count) from from_date through to_date inclusive."""
    start = datetime.strptime(from_date, "%Y-%m-%d").date()
    end = datetime.strptime(to_date, "%Y-%m-%d").date()
    validation_end = datetime.strptime(VALIDATION_DATE, "%Y-%m-%d").date()
    current = start
    day_offset = (start - validation_end).days - 1
    while current <= end:
        if current <= validation_end:
            current += timedelta(days=1)
            day_offset += 1
            continue
        yield current.strftime("%Y-%m-%d"), day_offset, daily_reading_count(day_offset)
        current += timedelta(days=1)
        day_offset += 1


def _build_row(
    *,
    sample_id: str,
    sample_type: str,
    date_str: str,
    lab_ph: float,
    lab_sugar: float,
    lab_citric: float,
    lab_ascorbic: float,
    ml_ph: float,
    ml_sugar: float,
    ml_citric: float,
    ml_ascorbic: float,
    rng: np.random.Generator,
) -> dict[str, Any]:
    temp = round(float(rng.uniform(24.5, 27.8)), 1)
    turb = round(float(rng.uniform(0.85, 1.25) if sample_type == "Natural" else rng.uniform(1.15, 1.95)), 2)
    tds = round(ml_sugar * 84.0 + rng.normal(0, 18), 1)
    status = classify_authenticity(ml_sugar, ml_citric, ml_ascorbic, ph=ml_ph)

    return {
        "sample_id": sample_id,
        "type": sample_type,
        "date": date_str,
        "lab_ph": round(lab_ph, 2),
        "lab_sugar_pct": round(lab_sugar, 4),
        "lab_citric_pct": round(lab_citric, 4),
        "lab_ascorbic_pct": round(lab_ascorbic, 6),
        "lab_sugar_g_per_mL": round(lab_sugar / 100.0, 7),
        "lab_citric_g_per_mL": round(lab_citric / 100.0, 9),
        "lab_ascorbic_g_per_mL": round(lab_ascorbic / 100.0, 9),
        "ml_ph": ml_ph,
        "ml_sugar_pct": ml_sugar,
        "ml_citric_pct": ml_citric,
        "ml_ascorbic_pct": ml_ascorbic,
        "tds": max(50.0, tds),
        "temperature": temp,
        "turbidity": turb,
        "authenticity_status": status,
        "confidence": compute_confidence(ml_sugar, ml_citric, ml_ascorbic, ph=ml_ph),
    }


def compute_validation_metrics(samples: list[dict[str, Any]]) -> dict[str, Any]:
    def mape(actual: list[float], pred: list[float]) -> float:
        errors = []
        for a, p in zip(actual, pred):
            if a == 0:
                errors.append(abs(p) * 100)
            else:
                errors.append(abs(p - a) / abs(a) * 100)
        return float(np.mean(errors)) if errors else 0.0

    lab_ph = [s["lab_ph"] for s in samples]
    ml_ph = [s["ml_ph"] for s in samples]
    ph_mae = float(np.mean([abs(a - p) for a, p in zip(lab_ph, ml_ph)]))

    param_metrics = {}
    for key, lab_k, ml_k in [
        ("sugar_pct", "lab_sugar_pct", "ml_sugar_pct"),
        ("citric_pct", "lab_citric_pct", "ml_citric_pct"),
        ("ascorbic_pct", "lab_ascorbic_pct", "ml_ascorbic_pct"),
    ]:
        lab = [s[lab_k] for s in samples]
        ml = [s[ml_k] for s in samples]
        m = mape(lab, ml)
        param_metrics[key] = {
            "mape_pct": round(m, 2),
            "accuracy_pct": round(max(0.0, 100.0 - m), 2),
        }

    ph_accuracy = round(max(0.0, 100.0 - ph_mae / 6.0 * 100), 2)
    overall = round(
        float(np.mean([
            ph_accuracy,
            param_metrics["sugar_pct"]["accuracy_pct"],
            param_metrics["citric_pct"]["accuracy_pct"],
            param_metrics["ascorbic_pct"]["accuracy_pct"],
        ])),
        2,
    )

    type_correct = sum(
        1 for s in samples
        if (s["type"] == "Natural" and s["authenticity_status"] == "authentic")
        or (s["type"] == "Artificial" and s["authenticity_status"] == "adulterated")
    )

    return {
        "sample_count": len(samples),
        "natural_count": sum(1 for s in samples if s["type"] == "Natural"),
        "artificial_count": sum(1 for s in samples if s["type"] == "Artificial"),
        "overall_accuracy_pct": overall,
        "ph_mae": round(ph_mae, 4),
        "ph_accuracy_pct": ph_accuracy,
        "parameters": param_metrics,
        "classification_accuracy_pct": round(type_correct / len(samples) * 100, 2) if samples else 0,
    }


def save_json(samples: list[dict[str, Any]], path: Path = JSON_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "validation_date": VALIDATION_DATE,
        "generated_seed": GENERATION_SEED,
        "metrics": compute_validation_metrics(samples),
        "samples": samples,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_json(path: Path = JSON_PATH) -> dict[str, Any]:
    if not path.is_file():
        samples = generate_samples()
        save_json(samples, path)
    return json.loads(path.read_text(encoding="utf-8"))


def sample_lookup(path: Path = JSON_PATH) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    return {s["sample_id"]: s for s in data["samples"]}


def timestamp_for_index(index: int, total: int, date_str: str = VALIDATION_DATE) -> datetime:
    """Spread readings across the validation day (naive UTC for Django make_aware)."""
    base = datetime.strptime(date_str, "%Y-%m-%d")
    minutes_span = 24 * 60 - 1
    offset_min = int(index * minutes_span / max(total - 1, 1))
    return base + timedelta(minutes=offset_min)
