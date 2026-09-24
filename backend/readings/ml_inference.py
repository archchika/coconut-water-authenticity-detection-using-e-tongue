"""
Run ML_1 (citric, ascorbic) + ML_2 (sugar) on sensor readings.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Natural ranges — aligned with frontend naturalReference (pH + composition)
NATURAL_RANGES = {
    "ph": (4.7, 6.32),
    "sugar": (1.8, 7.0),
    "citric": (0.04, 0.15),
    # Literature maturation ascorbic ~0.95–3.2 mg/100 mL → 0.00095–0.0032 % w/v
    "ascorbic": (0.0008, 0.0035),
}


def _in_range(value: float, low: float, high: float) -> bool:
    return low <= value <= high


def classify_authenticity(
    sugar: float,
    citric: float,
    ascorbic: float,
    ph: float | None = None,
) -> str:
    """
    Authentic only if sugar, citric, ascorbic (and pH when provided) are all
    inside natural coconut-water ranges.
    """
    ok = (
        _in_range(sugar, *NATURAL_RANGES["sugar"])
        and _in_range(citric, *NATURAL_RANGES["citric"])
        and _in_range(ascorbic, *NATURAL_RANGES["ascorbic"])
    )
    if ph is not None:
        ok = ok and _in_range(ph, *NATURAL_RANGES["ph"])
    return "authentic" if ok else "adulterated"


# Prototype system never reports absolute certainty.
PROTOTYPE_MAX_CONFIDENCE = 0.95
PROTOTYPE_MIN_CONFIDENCE = 0.52


def _range_fit_score(value: float, low: float, high: float) -> float:
    """In-range fit: 1.0 at midpoint, 0.0 at boundaries."""
    if not _in_range(value, low, high):
        return 0.0
    mid = (low + high) / 2.0
    half_span = (high - low) / 2.0
    if half_span <= 0:
        return 1.0
    return max(0.0, 1.0 - abs(value - mid) / half_span)


def _param_violation_severity(value: float, low: float, high: float) -> float:
    """Out-of-range severity: 0 in range, up to 1.0 when far outside."""
    if _in_range(value, low, high):
        return 0.0
    span = max(high - low, 1e-12)
    excess = (low - value) if value < low else (value - high)
    return min(1.0, excess / (span * 0.5))


def compute_confidence(
    sugar: float,
    citric: float,
    ascorbic: float,
    ph: float | None = None,
) -> float:
    """
    Prototype confidence in the authenticity classification (0.52–0.95).

    Authentic: how well pH + composition values sit inside natural ranges
    (centered readings score higher; edge-of-range readings score lower).

    Adulterated: how far out of range the failing parameters are, plus a small
    boost when more than one parameter fails. Never reaches 100% on prototype hardware.
    """
    params: list[tuple[float, tuple[float, float]]] = [
        (sugar, NATURAL_RANGES["sugar"]),
        (citric, NATURAL_RANGES["citric"]),
        (ascorbic, NATURAL_RANGES["ascorbic"]),
    ]
    if ph is not None:
        params.insert(0, (ph, NATURAL_RANGES["ph"]))
    status = classify_authenticity(sugar, citric, ascorbic, ph=ph)

    if status == "adulterated":
        severities = [_param_violation_severity(v, lo, hi) for v, (lo, hi) in params]
        avg_severity = sum(severities) / len(severities)
        failing_count = sum(1 for s in severities if s > 0)
        multi_param_boost = max(0, failing_count - 1) * 0.06
        raw = 0.58 + 0.30 * avg_severity + multi_param_boost
    else:
        fits = [_range_fit_score(v, lo, hi) for v, (lo, hi) in params]
        avg_fit = sum(fits) / len(fits)
        min_fit = min(fits)
        blended_fit = 0.6 * avg_fit + 0.4 * min_fit
        raw = 0.55 + 0.33 * blended_fit

    clamped = max(PROTOTYPE_MIN_CONFIDENCE, min(PROTOTYPE_MAX_CONFIDENCE, raw))
    return round(clamped, 4)


def predict_composition(
    ph: float,
    tds: float,
    temperature: float,
    turbidity: float,
) -> dict[str, Any]:
    from ML_1.predict import predict as predict_acids
    from ML_2.predict import predict as predict_sugar

    acids = predict_acids(pH=ph, temperature=temperature)
    sugar_out = predict_sugar(pH=ph, tds=tds, temperature=temperature, turbidity=turbidity)

    sugar = float(sugar_out["sugar_pct"])
    citric = float(acids["citric_percent_wv"])
    ascorbic = float(acids["ascorbic_percent_wv"])
    status = classify_authenticity(sugar, citric, ascorbic, ph=ph)

    return {
        "pH": round(ph, 2),
        "tds": round(tds, 1),
        "temperature": round(temperature, 1),
        "turbidity": round(turbidity, 1),
        "predicted_sugar": round(sugar, 4),
        "predicted_citric": round(citric, 4),
        "predicted_ascorbic": round(ascorbic, 4),
        "authenticity_status": status,
        "confidence": compute_confidence(sugar, citric, ascorbic, ph=ph),
    }


def predict_batch(raw_readings: list[dict[str, Any]]) -> dict[str, Any]:
    """Fuse each raw sample, run ML, return 3 predictions + average."""
    from .fusion_service import fuse_samples_for_ml

    fused = fuse_samples_for_ml(raw_readings)
    results = []
    for f in fused:
        results.append(
            predict_composition(
                ph=f["pH"],
                tds=f["tds"],
                temperature=f["temperature"],
                turbidity=f["turbidity"],
            )
        )

    n = len(results)
    avg = {
        "pH": round(sum(r["pH"] for r in results) / n, 2),
        "tds": round(sum(r["tds"] for r in results) / n, 1),
        "temperature": round(sum(r["temperature"] for r in results) / n, 1),
        "turbidity": round(sum(r["turbidity"] for r in results) / n, 1),
        "predicted_sugar": round(sum(r["predicted_sugar"] for r in results) / n, 4),
        "predicted_citric": round(sum(r["predicted_citric"] for r in results) / n, 4),
        "predicted_ascorbic": round(sum(r["predicted_ascorbic"] for r in results) / n, 4),
    }
    avg["authenticity_status"] = classify_authenticity(
        avg["predicted_sugar"],
        avg["predicted_citric"],
        avg["predicted_ascorbic"],
        ph=avg["pH"],
    )
    avg["confidence"] = compute_confidence(
        avg["predicted_sugar"],
        avg["predicted_citric"],
        avg["predicted_ascorbic"],
        ph=avg["pH"],
    )

    return {
        "readings": results,
        "fused_sensors": fused,
        "average": avg,
    }
