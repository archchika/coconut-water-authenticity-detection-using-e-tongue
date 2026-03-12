"""
Phase 5.5 — Upload API view: POST /api/upload-data/; save to DB; create Alert/SystemLog when adulterated.
Phase 5.6 — Aggregation views: GET /api/daily/, /api/weekly/, /api/monthly/.
Phase 6.5 — Admin list views: GET /api/readings/, /api/predictions/ with date/status filters (auth required).
Phase 6.8 — Rate limiting on upload endpoint.
"""
from datetime import datetime, timezone as dt_timezone

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response


class UploadRateThrottle(UserRateThrottle):
    """Phase 6.8 — Throttle POST /api/upload-data/ (rate set in settings DEFAULT_THROTTLE_RATES['upload'])."""
    scope = "upload"

from .models import SensorReading, Prediction
from .serializers import UploadPayloadSerializer, SensorReadingListSerializer, PredictionListSerializer
from .aggregation import aggregate_daily, aggregate_weekly, aggregate_monthly
from alerts.models import Alert
from logs.models import SystemLog
from core.constants import SENSOR_RANGES


class UploadDataView(APIView):
    """
    POST /api/upload-data/
    Body: { timestamp, pH, tds, temperature, turbidity, predicted_sugar, predicted_citric, predicted_ascorbic, status [, confidence, source_device_id ] }
    Creates SensorReading and Prediction; if status=adulterated, creates Alert and SystemLog (Phase 5.8).
    Phase 6.8: rate-limited via UploadRateThrottle (e.g. 60/hour per user); auth required.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UploadRateThrottle]

    def post(self, request):
        serializer = UploadPayloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ts = data["timestamp"]
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone=dt_timezone.utc)

        reading = SensorReading.objects.create(
            timestamp=ts,
            ph=data["pH"],
            tds=data["tds"],
            temperature=data["temperature"],
            turbidity=data["turbidity"],
            source_device_id=data.get("source_device_id") or None,
        )
        prediction = Prediction.objects.create(
            reading=reading,
            timestamp=ts,
            predicted_sugar=data["predicted_sugar"],
            predicted_citric=data["predicted_citric"],
            predicted_ascorbic=data["predicted_ascorbic"],
            authenticity_status=data["status"],
            confidence=data.get("confidence"),
        )

        # Phase 5.8: log abnormal cases — adulteration
        if data["status"] == "adulterated":
            Alert.objects.create(
                reading=reading,
                type="adulteration",
                message=f"Upload: authenticity_status=adulterated (sugar={data['predicted_sugar']:.4f}, citric={data['predicted_citric']:.4f}, ascorbic={data['predicted_ascorbic']:.4f})",
            )
            SystemLog.objects.create(
                level="WARNING",
                component="upload",
                message="Adulterated sample uploaded",
                metadata={
                    "reading_id": reading.id,
                    "prediction_id": prediction.id,
                    "predicted_sugar": data["predicted_sugar"],
                    "predicted_citric": data["predicted_citric"],
                    "predicted_ascorbic": data["predicted_ascorbic"],
                },
            )

        # Phase 5.8: log abnormal cases — sensor out-of-range
        sensor_values = {"ph": data["pH"], "tds": data["tds"], "temperature": data["temperature"], "turbidity": data["turbidity"]}
        out_of_range = []
        for name, (lo, hi) in SENSOR_RANGES.items():
            v = sensor_values.get(name)
            if v is not None and (v < lo or v > hi):
                out_of_range.append(f"{name}={v} (allowed {lo}-{hi})")
        if out_of_range:
            Alert.objects.create(
                reading=reading,
                type="out_of_range",
                message="Upload: sensor value(s) out of range: " + "; ".join(out_of_range),
            )
            SystemLog.objects.create(
                level="WARNING",
                component="upload",
                message="Sensor out-of-range on upload",
                metadata={"reading_id": reading.id, "out_of_range": out_of_range, "sensor_values": sensor_values},
            )

        return Response(
            {
                "reading_id": reading.id,
                "prediction_id": prediction.id,
                "timestamp": ts.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class DailyAggregationView(APIView):
    """GET /api/daily/?date=YYYY-MM-DD — aggregated data for one day (Phase 5.6). Public, no auth required."""
    permission_classes = [AllowAny]

    def get(self, request):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"error": "Missing query param: date (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date; use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = aggregate_daily(date)
            return Response(data)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {e}", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WeeklyAggregationView(APIView):
    """GET /api/weekly/?year=YYYY&week=W — aggregated data for ISO week (Phase 5.6). Public."""
    permission_classes = [AllowAny]

    def get(self, request):
        year = request.query_params.get("year")
        week = request.query_params.get("week")
        if not year or not week:
            return Response(
                {"error": "Missing query params: year, week (e.g. year=2025&week=8)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            year, week = int(year), int(week)
            if not (1 <= week <= 53):
                raise ValueError("week must be 1-53")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid year or week"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = aggregate_weekly(year, week)
            return Response(data)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {e}", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MonthlyAggregationView(APIView):
    """GET /api/monthly/?year=YYYY&month=M — aggregated data for calendar month (Phase 5.6). Public."""
    permission_classes = [AllowAny]

    def get(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        if not year or not month:
            return Response(
                {"error": "Missing query params: year, month (e.g. year=2025&month=2)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            year, month = int(year), int(month)
            if not (1 <= month <= 12):
                raise ValueError("month must be 1-12")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid year or month"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = aggregate_monthly(year, month)
            return Response(data)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {e}", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def _parse_date_range(request):
    """Parse optional date_from, date_to (YYYY-MM-DD) from query params. Returns (start, end) or (None, None)."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    start, end = None, None
    if date_from:
        try:
            start = timezone.make_aware(
                datetime.strptime(date_from, "%Y-%m-%d"),
                timezone=dt_timezone.utc,
            )
        except ValueError:
            pass
    if date_to:
        try:
            end = timezone.make_aware(
                datetime.strptime(date_to, "%Y-%m-%d"),
                timezone=dt_timezone.utc,
            )
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            pass
    return start, end


class SensorReadingListView(APIView):
    """GET /api/readings/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&limit=N (Phase 6.5). Auth required."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SensorReading.objects.all().order_by("-timestamp")
        start, end = _parse_date_range(request)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        limit = min(int(request.query_params.get("limit", 50)), 500)
        qs = qs[:limit]
        serializer = SensorReadingListSerializer(qs, many=True)
        return Response(serializer.data)


class PredictionListView(APIView):
    """GET /api/predictions/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&status=authentic|adulterated&limit=N (Phase 6.5). Auth required."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Prediction.objects.all().select_related("reading").order_by("-timestamp")
        start, end = _parse_date_range(request)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        status_val = request.query_params.get("status")
        if status_val in ("authentic", "adulterated"):
            qs = qs.filter(authenticity_status=status_val)
        limit = min(int(request.query_params.get("limit", 50)), 500)
        qs = qs[:limit]
        serializer = PredictionListSerializer(qs, many=True)
        return Response(serializer.data)
