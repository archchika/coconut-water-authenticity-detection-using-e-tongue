"""
Phase 5.4 — System operational log (Phase 5.4).
"""
from django.db import models


class SystemLog(models.Model):
    """Operational log entry (Phase 5.4)."""
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    level = models.CharField(max_length=16, db_index=True)  # e.g. INFO, WARNING, ERROR
    component = models.CharField(max_length=64, blank=True)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "logs_systemlogs"
        ordering = ["-timestamp"]
        verbose_name_plural = "System logs"

    def __str__(self):
        return f"SystemLog {self.level} {self.id} @ {self.timestamp}"
