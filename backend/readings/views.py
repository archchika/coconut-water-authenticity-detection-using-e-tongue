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
from .serializers import (
    UploadPayloadSerializer,
    SensorReadingListSerializer,
    PredictionListSerializer,
    DailyReadingsSerializer,
    ValidationSummarySerializer,
    PredictInputSerializer,
    PredictBatchSerializer,
    Esp32ReadingSerializer,
    Esp32RobotStatusSerializer,
)
from .aggregation import aggregate_daily, aggregate_weekly, aggregate_monthly, local_day_bounds
from .june30_validation import VALIDATION_DATE, load_json, sample_lookup
from .ml_inference import predict_composition, predict_batch, compute_confidence
from .esp32_ingest import (
    process_esp32_reading,
    get_live_status,
    update_robot_stage,
    clear_live_session,
)
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
            confidence=data.get("confidence")
            if data.get("confidence") is not None
            else compute_confidence(
                data["predicted_sugar"],
                data["predicted_citric"],
                data["predicted_ascorbic"],
                ph=data.get("pH"),
            ),
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
    """Parse optional date_from, date_to (YYYY-MM-DD) as local calendar days. Returns (start, end exclusive)."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    start, end = None, None
    if date_from:
        try:
            start, _ = local_day_bounds(datetime.strptime(date_from, "%Y-%m-%d").date())
        except ValueError:
            pass
    if date_to:
        try:
            _, end = local_day_bounds(datetime.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            pass
    return start, end


class DailyReadingsListView(APIView):
    """GET /api/daily/readings/?date=YYYY-MM-DD — list of predictions with readings for a day. Public."""

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
        start, end = local_day_bounds(date)
        predictions = (
            Prediction.objects.filter(timestamp__gte=start, timestamp__lt=end)
            .select_related("reading")
            .order_by("-timestamp")
        )
        ref_by_sample = sample_lookup() if date_str == VALIDATION_DATE else {}
        rows = []
        for p in predictions:
            reading = p.reading
            dt = p.timestamp
            if timezone.is_aware(dt):
                dt = timezone.localtime(dt)
            row = {
                "id": p.id,
                "reading": p.reading_id,
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"),
                "ph": reading.ph if reading else 0,
                "predicted_sugar": p.predicted_sugar,
                "predicted_citric": p.predicted_citric,
                "predicted_ascorbic": p.predicted_ascorbic,
                "authenticity_status": p.authenticity_status,
                "confidence": p.confidence,
            }
            sample_id = reading.source_device_id if reading else None
            if sample_id and sample_id in ref_by_sample:
                ref = ref_by_sample[sample_id]
                row.update({
                    "sample_id": sample_id,
                    "sample_type": ref["type"],
                    "lab_ph": ref["lab_ph"],
                    "lab_sugar_pct": ref["lab_sugar_pct"],
                    "lab_citric_pct": ref["lab_citric_pct"],
                    "lab_ascorbic_pct": ref["lab_ascorbic_pct"],
                })
            rows.append(row)
        serializer = DailyReadingsSerializer(rows, many=True)
        return Response(serializer.data)


class ValidationSummaryView(APIView):
    """GET /api/validation/summary/?date=YYYY-MM-DD — prototype lab vs ML accuracy summary."""

    permission_classes = [AllowAny]

    def get(self, request):
        date_str = request.query_params.get("date", VALIDATION_DATE)
        if date_str != VALIDATION_DATE:
            return Response(
                {"error": f"Validation summary only available for {VALIDATION_DATE}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            data = load_json()
        except OSError:
            return Response(
                {"error": "Validation dataset not found. Run: python manage.py load_june30_validation"},
                status=status.HTTP_404_NOT_FOUND,
            )
        payload = {
            "validation_date": data["validation_date"],
            **data["metrics"],
        }
        serializer = ValidationSummarySerializer(payload)
        return Response(serializer.data)


class SensorReadingListView(APIView):
    """GET /api/readings/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&limit=N (Phase 6.5). Auth required."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SensorReading.objects.all().order_by("-timestamp")
        start, end = _parse_date_range(request)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lt=end)
        limit = min(int(request.query_params.get("limit", 50)), 1000)
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
            qs = qs.filter(timestamp__lt=end)
        status_val = request.query_params.get("status")
        if status_val in ("authentic", "adulterated"):
            qs = qs.filter(authenticity_status=status_val)
        limit = min(int(request.query_params.get("limit", 50)), 1000)
        qs = qs[:limit]
        serializer = PredictionListSerializer(qs, many=True)
        return Response(serializer.data)


class PredictCompositionView(APIView):
    """POST /api/predict/ — ML_1 + ML_2 inference from sensor readings. Public (admin UI)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PredictInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        try:
            result = predict_composition(
                ph=data["pH"],
                tds=data["tds"],
                temperature=data["temperature"],
                turbidity=data["turbidity"],
            )
            return Response(result)
        except FileNotFoundError as e:
            return Response(
                {"error": str(e), "detail": "Train ML models: python ML_1/train_model.py && python ML_2/train_model.py"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": f"Prediction failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PredictBatchView(APIView):
    """POST /api/predict-batch/ — fuse + ML on first 3 raw sensor snapshots."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PredictBatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            raw = serializer.validated_data["readings"]
            result = predict_batch(raw)
            return Response(result)
        except FileNotFoundError as e:
            return Response(
                {"error": str(e), "detail": "Train ML models: python ML_1/train_model.py && python ML_2/train_model.py"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": f"Batch prediction failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class Esp32ReadingView(APIView):
    """
    POST /api/esp32-reading/
    Accept one ESP32 wireless JSON payload per request.
    Buffers 3 readings per device → sensor fusion → ML → saves to DB.
    No auth (factory LAN / ESP32).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Esp32ReadingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        fallback_key = request.META.get("REMOTE_ADDR") or "esp32-default"
        try:
            result = process_esp32_reading(dict(data), fallback_key)
            if result["status"] == "buffered":
                return Response(result, status=status.HTTP_202_ACCEPTED)
            return Response(result, status=status.HTTP_201_CREATED)
        except FileNotFoundError as e:
            return Response(
                {"error": str(e), "detail": "Train ML models: python ML_1/train_model.py && python ML_2/train_model.py"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": f"ESP32 ingest failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class Esp32RobotStatusView(APIView):
    """POST /api/esp32-status/ — update the arm station shown on the dashboard."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Esp32RobotStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        robot_status = update_robot_stage(
            stage=data["stage"],
            source_device_id=data.get("source_device_id"),
        )
        return Response(robot_status, status=status.HTTP_200_OK)


class Esp32LiveView(APIView):
    """GET /api/esp32-live/ — buffered + latest sensor values for admin dashboard.
    DELETE /api/esp32-live/ — clear in-memory test/stale live batch (not DB history).
    """

    # Public on the factory LAN so the live robot display works without an
    # expiring browser token. Historical/admin APIs remain authenticated.
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(get_live_status())

    def delete(self, request):
        return Response(clear_live_session())
