"""
Phase 5.4 — Sensor readings, predictions, and optional calibration metadata.
"""
from django.db import models


class SensorReading(models.Model):
    """Raw/fused sensor data from device or gateway (Phase 5.4)."""
    timestamp = models.DateTimeField(db_index=True)
    ph = models.FloatField()
    tds = models.FloatField()
    temperature = models.FloatField()
    turbidity = models.FloatField()
    source_device_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        db_table = "readings_sensorreadings"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"SensorReading {self.id} @ {self.timestamp}"


class Prediction(models.Model):
    """ML outputs linked to a sensor reading (Phase 5.4)."""
    reading = models.OneToOneField(
        SensorReading,
        on_delete=models.CASCADE,
        related_name="prediction",
    )
    timestamp = models.DateTimeField(db_index=True)
    predicted_sugar = models.FloatField()
    predicted_citric = models.FloatField()
    predicted_ascorbic = models.FloatField()
    authenticity_status = models.CharField(max_length=32, db_index=True)  # e.g. authentic, adulterated
    confidence = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "readings_predictions"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Prediction {self.id} {self.authenticity_status} @ {self.timestamp}"


class CalibrationData(models.Model):
    """Optional: calibration run metadata or baseline values for traceability (Phase 5.4)."""
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    run_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # e.g. baseline values, notes

    class Meta:
        db_table = "readings_calibrationdata"
        ordering = ["-timestamp"]
        verbose_name_plural = "Calibration data"

    def __str__(self):
        return f"CalibrationData {self.id} ({self.run_id or 'no run_id'})"
