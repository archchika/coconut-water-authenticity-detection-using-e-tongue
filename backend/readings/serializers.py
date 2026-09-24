"""
Phase 5.5 — Serializers for upload payload.
Phase 6.5 — List serializers for admin API (readings, predictions).
"""
from rest_framework import serializers

from .models import SensorReading, Prediction


class UploadPayloadSerializer(serializers.Serializer):
    """Validate POST /api/upload-data/ body (Phase 5.1, 5.5)."""
    timestamp = serializers.DateTimeField(required=True)
    pH = serializers.FloatField(required=True)
    tds = serializers.FloatField(required=True)
    temperature = serializers.FloatField(required=True)
    turbidity = serializers.FloatField(required=True)
    predicted_sugar = serializers.FloatField(required=True)
    predicted_citric = serializers.FloatField(required=True)
    predicted_ascorbic = serializers.FloatField(required=True)
    status = serializers.ChoiceField(
        choices=["authentic", "adulterated"],
        required=True,
    )
    confidence = serializers.FloatField(required=False, allow_null=True)
    source_device_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")

    def to_internal_value(self, data):
        # Accept "ph" as alias for "pH"
        if "ph" in data and "pH" not in data:
            data = {**data, "pH": data["ph"]}
        return super().to_internal_value(data)


class SensorReadingListSerializer(serializers.ModelSerializer):
    """Phase 6.5 — List output for GET /api/readings/."""

    class Meta:
        model = SensorReading
        fields = ("id", "timestamp", "ph", "tds", "temperature", "turbidity", "source_device_id")


class PredictionListSerializer(serializers.ModelSerializer):
    """Phase 6.5 — List output for GET /api/predictions/. 'reading' is the SensorReading id."""

    class Meta:
        model = Prediction
        fields = (
            "id",
            "reading",
            "timestamp",
            "predicted_sugar",
            "predicted_citric",
            "predicted_ascorbic",
            "authenticity_status",
            "confidence",
        )


class DailyReadingsSerializer(serializers.Serializer):
    """Public list for GET /api/daily/readings/ — predictions with reading ph, for Quality page table."""

    id = serializers.IntegerField()
    reading = serializers.IntegerField()
    date = serializers.CharField()
    time = serializers.CharField()
    ph = serializers.FloatField()
    predicted_sugar = serializers.FloatField()
    predicted_citric = serializers.FloatField()
    predicted_ascorbic = serializers.FloatField()
    authenticity_status = serializers.CharField()
    confidence = serializers.FloatField(allow_null=True)
    sample_id = serializers.CharField(required=False, allow_null=True)
    sample_type = serializers.CharField(required=False, allow_null=True)
    lab_ph = serializers.FloatField(required=False, allow_null=True)
    lab_sugar_pct = serializers.FloatField(required=False, allow_null=True)
    lab_citric_pct = serializers.FloatField(required=False, allow_null=True)
    lab_ascorbic_pct = serializers.FloatField(required=False, allow_null=True)


class ValidationSummarySerializer(serializers.Serializer):
    """GET /api/validation/summary/ — prototype validation metrics for a date."""

    validation_date = serializers.CharField()
    sample_count = serializers.IntegerField()
    natural_count = serializers.IntegerField()
    artificial_count = serializers.IntegerField()
    overall_accuracy_pct = serializers.FloatField()
    ph_accuracy_pct = serializers.FloatField()
    ph_mae = serializers.FloatField()
    classification_accuracy_pct = serializers.FloatField()
    parameters = serializers.DictField()


class PredictInputSerializer(serializers.Serializer):
    """POST /api/predict/ — sensor inputs for ML inference."""

    pH = serializers.FloatField(required=True)
    tds = serializers.FloatField(required=True)
    temperature = serializers.FloatField(required=True)
    turbidity = serializers.FloatField(required=True)

    def to_internal_value(self, data):
        if "ph" in data and "pH" not in data:
            data = {**data, "pH": data["ph"]}
        return super().to_internal_value(data)


class PredictBatchSerializer(serializers.Serializer):
    """POST /api/predict-batch/ — three raw sensor snapshots."""

    readings = serializers.ListField(
        child=PredictInputSerializer(),
        min_length=3,
        max_length=3,
    )


class Esp32ReadingSerializer(serializers.Serializer):
    """POST /api/esp32-reading/ — single ESP32 JSON line (wireless)."""

    timestamp_ms = serializers.IntegerField(required=False)
    pH = serializers.FloatField(required=True)
    tds = serializers.FloatField(required=True)
    temperature = serializers.FloatField(required=True)
    turbidity = serializers.FloatField(required=True)
    status = serializers.CharField(required=False, allow_blank=True, default="unknown")
    source_device_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")

    def to_internal_value(self, data):
        if "ph" in data and "pH" not in data:
            data = {**data, "pH": data["ph"]}
        return super().to_internal_value(data)


class Esp32RobotStatusSerializer(serializers.Serializer):
    """POST /api/esp32-status/ — current robotic-arm station."""

    stage = serializers.ChoiceField(
        choices=(
            "initial_position",
            "detection_station",
            "cleaning_station",
            "drying_station",
            "idle",
        )
    )
    source_device_id = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )
