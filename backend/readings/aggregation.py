"""
Phase 5.6 — Aggregation helpers: date/week/month range and aggregate query.

Returns aggregated sensor + prediction averages and authenticity counts for frontend.
"""
import calendar
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone as django_timezone
from django.db.models import Avg, Count, Q

from .models import SensorReading, Prediction


def _round(val):
    return round(val, 4) if val is not None else None


def _aggregate_for_querysets(readings_qs, predictions_qs):
    """Compute averages and authenticity counts from two querysets (same time range)."""
    reading_ag = readings_qs.aggregate(
        ph=Avg("ph"),
        tds=Avg("tds"),
        temperature=Avg("temperature"),
        turbidity=Avg("turbidity"),
    )
    pred_ag = predictions_qs.aggregate(
        predicted_sugar=Avg("predicted_sugar"),
        predicted_citric=Avg("predicted_citric"),
        predicted_ascorbic=Avg("predicted_ascorbic"),
        authentic=Count("id", filter=Q(authenticity_status="authentic")),
        adulterated=Count("id", filter=Q(authenticity_status="adulterated")),
    )
    count = predictions_qs.count()
    return {
        "count": count,
        "averages": {
            "ph": _round(reading_ag.get("ph")),
            "tds": _round(reading_ag.get("tds")),
            "temperature": _round(reading_ag.get("temperature")),
            "turbidity": _round(reading_ag.get("turbidity")),
            "predicted_sugar": _round(pred_ag.get("predicted_sugar")),
            "predicted_citric": _round(pred_ag.get("predicted_citric")),
            "predicted_ascorbic": _round(pred_ag.get("predicted_ascorbic")),
        },
        "authenticity": {
            "authentic": pred_ag.get("authentic") or 0,
            "adulterated": pred_ag.get("adulterated") or 0,
        },
        "status": "authentic" if (pred_ag.get("adulterated") or 0) == 0 else "adulterated",
    }


def aggregate_daily(date):
    """date: date object (UTC day). Return aggregated stats for that day."""
    start = django_timezone.make_aware(datetime.combine(date, datetime.min.time()), dt_timezone.utc)
    end = start + timedelta(days=1)
    readings = SensorReading.objects.filter(timestamp__gte=start, timestamp__lt=end)
    predictions = Prediction.objects.filter(timestamp__gte=start, timestamp__lt=end)
    out = _aggregate_for_querysets(readings, predictions)
    out["period"] = date.isoformat()
    out["period_type"] = "daily"
    return out


def aggregate_weekly(year, week):
    """year, week: ISO year and week number. Return aggregated stats for that week."""
    # Monday of ISO week (Python 3.8+)
    d = datetime.fromisocalendar(int(year), int(week), 1)
    start = django_timezone.make_aware(datetime.combine(d.date(), datetime.min.time()), dt_timezone.utc)
    end = start + timedelta(days=7)
    readings = SensorReading.objects.filter(timestamp__gte=start, timestamp__lt=end)
    predictions = Prediction.objects.filter(timestamp__gte=start, timestamp__lt=end)
    out = _aggregate_for_querysets(readings, predictions)
    out["period"] = f"{year}-W{week:02d}"
    out["period_type"] = "weekly"
    return out


def aggregate_monthly(year, month):
    """year, month: calendar year and month (1-12). Return aggregated stats for that month."""
    start_d = datetime(int(year), int(month), 1).date()
    _, last_day = calendar.monthrange(int(year), int(month))
    end_d = datetime(int(year), int(month), last_day).date() + timedelta(days=1)
    start = django_timezone.make_aware(datetime.combine(start_d, datetime.min.time()), dt_timezone.utc)
    end = django_timezone.make_aware(datetime.combine(end_d, datetime.min.time()), dt_timezone.utc)
    readings = SensorReading.objects.filter(timestamp__gte=start, timestamp__lt=end)
    predictions = Prediction.objects.filter(timestamp__gte=start, timestamp__lt=end)
    out = _aggregate_for_querysets(readings, predictions)
    out["period"] = f"{year}-{month:02d}"
    out["period_type"] = "monthly"
    return out
