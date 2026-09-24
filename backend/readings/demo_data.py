"""Shared helpers to persist generated reading rows to the database."""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from typing import Any

from django.utils import timezone

from alerts.models import Alert
from readings.models import Prediction, SensorReading
from readings.june30_validation import timestamp_for_index


def persist_reading_rows(rows: list[dict[str, Any]], date_str: str) -> int:
    created = 0
    for i, row in enumerate(rows):
        ts = timezone.make_aware(
            timestamp_for_index(i, len(rows), date_str),
            timezone=dt_timezone.utc,
        )
        reading = SensorReading.objects.create(
            timestamp=ts,
            ph=row["ml_ph"],
            tds=row["tds"],
            temperature=row["temperature"],
            turbidity=row["turbidity"],
            source_device_id=row["sample_id"],
        )
        Prediction.objects.create(
            reading=reading,
            timestamp=ts,
            predicted_sugar=row["ml_sugar_pct"],
            predicted_citric=row["ml_citric_pct"],
            predicted_ascorbic=row["ml_ascorbic_pct"],
            authenticity_status=row["authenticity_status"],
            confidence=row["confidence"],
        )
        if row["authenticity_status"] == "adulterated":
            Alert.objects.create(
                reading=reading,
                type="adulteration",
                message=(
                    f"{date_str} {row['sample_id']}: adulterated "
                    f"(sugar={row['ml_sugar_pct']:.4f}%, citric={row['ml_citric_pct']:.4f}%)"
                ),
            )
        created += 1
    return created


def clear_readings_for_date(date_str: str) -> tuple[int, int]:
    start = timezone.make_aware(
        datetime.strptime(date_str, "%Y-%m-%d"),
        timezone=dt_timezone.utc,
    )
    end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
    preds = Prediction.objects.filter(timestamp__gte=start, timestamp__lte=end)
    reading_ids = list(preds.values_list("reading_id", flat=True))
    alert_count = Alert.objects.filter(reading_id__in=reading_ids).delete()[0]
    preds.delete()
    reading_count = SensorReading.objects.filter(id__in=reading_ids).delete()[0]
    return reading_count, alert_count


def clear_readings_in_range(from_date: str, to_date: str) -> tuple[int, int]:
    start = timezone.make_aware(
        datetime.strptime(from_date, "%Y-%m-%d"),
        timezone=dt_timezone.utc,
    )
    end = timezone.make_aware(
        datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999),
        timezone=dt_timezone.utc,
    )
    preds = Prediction.objects.filter(timestamp__gte=start, timestamp__lte=end)
    reading_ids = list(preds.values_list("reading_id", flat=True))
    alert_count = Alert.objects.filter(reading_id__in=reading_ids).delete()[0]
    preds.delete()
    reading_count = SensorReading.objects.filter(id__in=reading_ids).delete()[0]
    return reading_count, alert_count
