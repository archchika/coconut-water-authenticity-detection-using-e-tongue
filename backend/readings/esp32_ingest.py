"""
ESP32 wireless ingest: buffer 3 raw readings → fusion + ML → save to DB.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from django.utils import timezone

from alerts.models import Alert
from logs.models import SystemLog
from core.constants import SENSOR_RANGES

from .ml_inference import predict_batch
from .models import Prediction, SensorReading

logger = logging.getLogger(__name__)

REQUIRED_COUNT = 3
# Hide robot position if ESP32 stops updating (powered off / sketch finished).
ROBOT_STATUS_STALE_SECONDS = 180
# Shared file so ESP32 POSTs and the dashboard GET see the same live data
# even if two runserver processes are bound to port 8000.
_STATE_PATH = Path(__file__).resolve().parent / "esp32_live_state.json"
# DEMO force flags — keep False for live ML authenticity from real sensor data.
DEMO_FORCE_AUTHENTIC_DEVICE_IDS = frozenset({"robot-arm-esp32-01"})
DEMO_FORCE_AUTHENTIC = False
DEMO_FORCE_ADULTERATED = False
DEMO_FORCE_ADULTERATED_DEVICE_IDS = frozenset({"robot-arm-esp32-01"})

_lock = threading.Lock()
_buffers: dict[str, list[dict[str, Any]]] = {}
_buffer_slots: dict[str, list[dict[str, Any]]] = {}
_latest_live: dict[str, Any] | None = None
_latest_robot_status: dict[str, Any] | None = None
_latest_completed_batch: dict[str, Any] | None = None
_latest_cleaning: dict[str, Any] | None = None


def _load_state_unlocked() -> None:
    global _buffers, _buffer_slots, _latest_live, _latest_robot_status
    global _latest_completed_batch, _latest_cleaning
    if not _STATE_PATH.exists():
        return
    try:
        data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    _buffers = data.get("buffers") or {}
    _buffer_slots = data.get("buffer_slots") or {}
    _latest_live = data.get("latest_live")
    _latest_robot_status = data.get("latest_robot_status")
    _latest_completed_batch = data.get("latest_completed_batch")
    _latest_cleaning = data.get("latest_cleaning")


def _save_state_unlocked() -> None:
    payload = {
        "buffers": _buffers,
        "buffer_slots": _buffer_slots,
        "latest_live": _latest_live,
        "latest_robot_status": _latest_robot_status,
        "latest_completed_batch": _latest_completed_batch,
        "latest_cleaning": _latest_cleaning,
    }
    try:
        tmp = _STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, default=str), encoding="utf-8")
        tmp.replace(_STATE_PATH)
    except OSError:
        pass


def update_robot_stage(stage: str, source_device_id: str | None = None) -> dict[str, Any]:
    """Store the latest arm station for dashboard polling."""
    global _latest_robot_status
    if stage == "idle":
        # Keep last station on the dashboard; do not blank the lights.
        with _lock:
            if _latest_robot_status:
                return dict(_latest_robot_status)
        return {"stage": None, "source_device_id": None, "updated_at": timezone.now().isoformat()}
    status = {
        "stage": stage,
        "source_device_id": (source_device_id or "").strip() or None,
        "updated_at": timezone.now().isoformat(),
    }
    with _lock:
        _latest_robot_status = status
        _save_state_unlocked()
    return status


def clear_live_session() -> dict[str, Any]:
    """Drop in-memory ESP32 batch buffer and live snapshot (test/stale data)."""
    global _latest_live, _latest_robot_status, _latest_completed_batch, _latest_cleaning
    with _lock:
        _buffers.clear()
        _buffer_slots.clear()
        _latest_live = None
        _latest_robot_status = None
        _latest_completed_batch = None
        _latest_cleaning = None
        _save_state_unlocked()
    return get_live_status()


def _enrich_reading_with_ml(raw: dict[str, Any]) -> dict[str, Any]:
    """Run fusion + ML on one ESP32 reading for progressive UI columns."""
    from .fusion_service import fuse_samples_for_ml
    from .ml_inference import predict_composition

    fused = fuse_samples_for_ml([raw])[0]
    pred = predict_composition(
        ph=fused["pH"],
        tds=fused["tds"],
        temperature=fused["temperature"],
        turbidity=fused["turbidity"],
    )
    snap = _snapshot_raw(raw)
    return {
        **snap,
        "predicted_sugar": pred["predicted_sugar"],
        "predicted_citric": pred["predicted_citric"],
        "predicted_ascorbic": pred["predicted_ascorbic"],
        "authenticity_status": pred["authenticity_status"],
        "confidence": pred.get("confidence"),
    }


def device_key(source_device_id: str | None, fallback: str) -> str:
    sid = (source_device_id or "").strip()
    return sid or fallback


def append_and_maybe_flush(device_key: str, raw: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Append one reading. Returns exactly 3 raw dicts when ready, else None."""
    with _lock:
        buf = _buffers.setdefault(device_key, [])
        slots = _buffer_slots.setdefault(device_key, [])
        buf.append(raw)
        # Enrich with ML so First/Second columns show sugar, citric, ascorbic live.
        try:
            slots.append(_enrich_reading_with_ml(raw))
        except Exception:
            slots.append(_snapshot_raw(raw))
        if len(buf) < REQUIRED_COUNT:
            return None
        batch = buf[:REQUIRED_COUNT]
        _buffers[device_key] = buf[REQUIRED_COUNT:]
        _buffer_slots[device_key] = slots[REQUIRED_COUNT:]
        return batch


def buffered_count(device_key: str) -> int:
    with _lock:
        return len(_buffers.get(device_key, []))


def raw_to_predict_input(raw: dict[str, Any]) -> dict[str, float]:
    return {
        "pH": float(raw["pH"]),
        "tds": float(raw["tds"]),
        "temperature": float(raw["temperature"]),
        "turbidity": float(raw["turbidity"]),
    }


def persist_one_esp32_reading(
    raw: dict[str, Any],
    pred: dict[str, Any],
    source_device_id: str | None,
) -> int | None:
    """Save each ESP32 sample + ML result so the public Quality page can show it immediately."""
    ts = timezone.now()
    try:
        reading = SensorReading.objects.create(
            timestamp=ts,
            ph=pred.get("pH", raw.get("pH", 0)),
            tds=pred.get("tds", raw.get("tds", 0)),
            temperature=pred.get("temperature", raw.get("temperature", 0)),
            turbidity=pred.get("turbidity", raw.get("turbidity", 0)),
            source_device_id=source_device_id or None,
        )
        Prediction.objects.create(
            reading=reading,
            timestamp=ts,
            predicted_sugar=pred.get("predicted_sugar") or 0,
            predicted_citric=pred.get("predicted_citric") or 0,
            predicted_ascorbic=pred.get("predicted_ascorbic") or 0,
            authenticity_status=pred.get("authenticity_status") or "adulterated",
            confidence=pred.get("confidence"),
        )
        sensor_values = {
            "ph": reading.ph,
            "tds": reading.tds,
            "temperature": reading.temperature,
            "turbidity": reading.turbidity,
        }
        out_of_range = []
        for name, (lo, hi) in SENSOR_RANGES.items():
            v = sensor_values.get(name)
            if v is not None and (v < lo or v > hi):
                out_of_range.append(f"{name}={v} (allowed {lo}-{hi})")
        if out_of_range:
            Alert.objects.create(
                reading=reading,
                type="out_of_range",
                message="ESP32: sensor value(s) out of range: " + "; ".join(out_of_range),
            )
        return reading.id
    except Exception:
        logger.exception("Failed to persist ESP32 reading for website")
        return None


def persist_batch(
    batch_raw: list[dict[str, Any]],
    ml_result: dict[str, Any],
    source_device_id: str | None,
) -> dict[str, Any]:
    """Each sample is already saved. Update the last 3 with fused batch ML and raise alerts."""
    ts = timezone.now()
    recent = list(
        SensorReading.objects.filter(source_device_id=source_device_id or None).order_by("-id")[:3]
    )
    recent.reverse()
    reading_ids: list[int] = []
    prediction_ids: list[int] = []
    fused_rows = ml_result.get("readings") or []

    for reading, pred in zip(recent, fused_rows):
        reading.ph = pred["pH"]
        reading.tds = pred["tds"]
        reading.temperature = pred["temperature"]
        reading.turbidity = pred["turbidity"]
        reading.save(update_fields=["ph", "tds", "temperature", "turbidity"])
        prediction = getattr(reading, "prediction", None)
        if prediction:
            prediction.timestamp = ts
            prediction.predicted_sugar = pred["predicted_sugar"]
            prediction.predicted_citric = pred["predicted_citric"]
            prediction.predicted_ascorbic = pred["predicted_ascorbic"]
            prediction.authenticity_status = pred["authenticity_status"]
            prediction.confidence = pred.get("confidence")
            prediction.save()
            prediction_ids.append(prediction.id)
        reading_ids.append(reading.id)

    avg = ml_result["average"]
    if avg["authenticity_status"] == "adulterated" and reading_ids:
        last_reading = SensorReading.objects.get(pk=reading_ids[-1])
        Alert.objects.create(
            reading=last_reading,
            type="adulteration",
            message=(
                f"ESP32 batch: adulterated (sugar={avg['predicted_sugar']:.4f}, "
                f"citric={avg['predicted_citric']:.4f}, ascorbic={avg['predicted_ascorbic']:.4f})"
            ),
        )
        SystemLog.objects.create(
            level="WARNING",
            component="esp32",
            message="Adulterated sample from ESP32 wireless batch",
            metadata={
                "reading_ids": reading_ids,
                "prediction_ids": prediction_ids,
                "average": avg,
            },
        )

    return {
        "reading_ids": reading_ids,
        "prediction_ids": prediction_ids,
        "timestamp": ts.isoformat(),
    }


def _is_cleaning_payload(raw: dict[str, Any]) -> bool:
    status = str(raw.get("status") or "").strip().lower()
    station = str(raw.get("station") or "").strip().lower()
    return status in {"cleaning", "cleaning_station"} or station in {
        "cleaning",
        "cleaning_station",
    }


def store_cleaning_reading(raw: dict[str, Any]) -> dict[str, Any]:
    """Keep rinse-station sensors for the dashboard; do not add to the ML batch of 3."""
    global _latest_cleaning
    snap = {
        "pH": float(raw["pH"]),
        "tds": float(raw["tds"]),
        "temperature": float(raw["temperature"]),
        "turbidity": float(raw["turbidity"]),
        "source_device_id": raw.get("source_device_id"),
        "updated_at": timezone.now().isoformat(),
    }
    with _lock:
        _load_state_unlocked()
        _latest_cleaning = snap
        _save_state_unlocked()
    return {
        "status": "cleaning",
        "latest_cleaning": snap,
        "message": "Cleaning-station reading stored for verification (not used for authenticity ML).",
    }


def _snapshot_raw(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "pH": float(raw["pH"]),
        "tds": float(raw["tds"]),
        "temperature": float(raw["temperature"]),
        "turbidity": float(raw["turbidity"]),
        "source_device_id": raw.get("source_device_id"),
    }


def get_live_status() -> dict[str, Any]:
    """Buffer state + latest saved reading for admin UI live polling."""
    with _lock:
        _load_state_unlocked()
        max_buffered = 0
        latest_buffered: dict[str, Any] | None = None
        active_buffer: list[dict[str, Any]] = []
        active_slots: list[dict[str, Any]] = []
        for key, buf in _buffers.items():
            if len(buf) > max_buffered:
                max_buffered = len(buf)
                active_buffer = list(buf)
                active_slots = list(_buffer_slots.get(key, []))
            if buf:
                latest_buffered = buf[-1]

    latest_reading = SensorReading.objects.order_by("-timestamp").first()
    latest_saved = None
    if latest_reading:
        latest_saved = {
            "id": latest_reading.id,
            "timestamp": latest_reading.timestamp.isoformat(),
            "pH": latest_reading.ph,
            "tds": latest_reading.tds,
            "temperature": latest_reading.temperature,
            "turbidity": latest_reading.turbidity,
            "source_device_id": latest_reading.source_device_id,
        }

    current = None
    with _lock:
        live = _latest_live
    if live:
        current = {
            "pH": float(live["pH"]),
            "tds": float(live["tds"]),
            "temperature": float(live["temperature"]),
            "turbidity": float(live["turbidity"]),
            "source_device_id": live.get("source_device_id"),
        }
    elif latest_buffered:
        current = {
            "pH": float(latest_buffered["pH"]),
            "tds": float(latest_buffered["tds"]),
            "temperature": float(latest_buffered["temperature"]),
            "turbidity": float(latest_buffered["turbidity"]),
            "source_device_id": latest_buffered.get("source_device_id"),
        }
    # Do not fall back to latest_saved — that re-shows old/test rows on Home.

    with _lock:
        robot_status = dict(_latest_robot_status) if _latest_robot_status else None
        completed_batch = dict(_latest_completed_batch) if _latest_completed_batch else None
        latest_cleaning = dict(_latest_cleaning) if _latest_cleaning else None

    if robot_status and robot_status.get("updated_at"):
        try:
            from datetime import datetime, timezone as dt_tz

            raw_ts = str(robot_status["updated_at"]).replace("Z", "+00:00")
            updated = datetime.fromisoformat(raw_ts)
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=dt_tz.utc)
            age = (timezone.now() - updated).total_seconds()
            if age > ROBOT_STATUS_STALE_SECONDS:
                robot_status = None
        except (TypeError, ValueError):
            pass

    return {
        "buffered_count": max_buffered,
        "required_count": REQUIRED_COUNT,
        "buffered_readings": active_slots[:max_buffered] if active_slots else [_snapshot_raw(r) for r in active_buffer],
        "current": current,
        "latest_saved": latest_saved,
        "robot_status": robot_status,
        "completed_batch": completed_batch,
        "latest_cleaning": latest_cleaning,
    }


def process_esp32_reading(raw: dict[str, Any], device_key_str: str) -> dict[str, Any]:
    """
    Buffer one ESP32 payload. When 3 collected: fusion → ML → DB.
    Returns response dict with status buffered|complete|cleaning.
    """
    if _is_cleaning_payload(raw):
        return store_cleaning_reading(raw)

    global _latest_live
    with _lock:
        _latest_live = {
            "pH": float(raw["pH"]),
            "tds": float(raw["tds"]),
            "temperature": float(raw["temperature"]),
            "turbidity": float(raw["turbidity"]),
            "source_device_id": raw.get("source_device_id"),
        }
        _save_state_unlocked()

    sid = raw.get("source_device_id")
    key = device_key(sid, device_key_str)
    try:
        persist_one_esp32_reading(raw, _enrich_reading_with_ml(raw), sid or key)
    except Exception:
        logger.exception("ESP32 live ML enrich/persist failed")
        persist_one_esp32_reading(raw, _snapshot_raw(raw), sid or key)
    batch = append_and_maybe_flush(key, raw)
    with _lock:
        _save_state_unlocked()

    if batch is None:
        count = buffered_count(key)
        return {
            "status": "buffered",
            "device_id": key,
            "buffered_count": count,
            "required_count": REQUIRED_COUNT,
            "message": f"Reading {count}/{REQUIRED_COUNT} stored; send {REQUIRED_COUNT - count} more.",
        }

    predict_inputs = [raw_to_predict_input(r) for r in batch]
    try:
        ml_result = predict_batch(predict_inputs)
    except FileNotFoundError as e:
        return {
            "status": "buffered",
            "device_id": key,
            "buffered_count": REQUIRED_COUNT,
            "required_count": REQUIRED_COUNT,
            "error": str(e),
            "message": "Received 3 readings but ML models missing. Train ML_1 and ML_2.",
            "current": _latest_live,
        }

    # DEMO: force authenticity label for robot-arm device after all 3 readings.
    device_id = (sid or key or "").strip()
    if DEMO_FORCE_AUTHENTIC and device_id in DEMO_FORCE_AUTHENTIC_DEVICE_IDS:
        ml_result["average"]["authenticity_status"] = "authentic"
        for row in ml_result.get("readings", []):
            row["authenticity_status"] = "authentic"
    elif DEMO_FORCE_ADULTERATED and device_id in DEMO_FORCE_ADULTERATED_DEVICE_IDS:
        ml_result["average"]["authenticity_status"] = "adulterated"
        for row in ml_result.get("readings", []):
            row["authenticity_status"] = "adulterated"

    saved = persist_batch(batch, ml_result, sid or key)

    global _latest_completed_batch
    with _lock:
        _latest_completed_batch = {
            "readings": ml_result.get("readings", []),
            "average": ml_result.get("average", {}),
            "timestamp": saved.get("timestamp"),
            "device_id": key,
        }
        _save_state_unlocked()

    return {
        "status": "complete",
        "device_id": key,
        **ml_result,
        **saved,
    }
