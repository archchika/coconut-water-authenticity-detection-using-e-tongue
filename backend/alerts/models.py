"""
Phase 5.4 — Alerts (adulteration, sensor fault, out-of-range, etc.).
"""
from django.db import models


class Alert(models.Model):
    """Abnormal event; optionally linked to a reading (Phase 5.4)."""
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    type = models.CharField(max_length=64, db_index=True)  # e.g. adulteration, sensor_fault, out_of_range
    message = models.TextField(blank=True)
    reading = models.ForeignKey(
        "readings.SensorReading",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    resolved = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "alerts_alerts"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Alert {self.id} {self.type} (resolved={self.resolved})"
