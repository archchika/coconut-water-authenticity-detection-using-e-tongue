from django.contrib import admin
from .models import SensorReading, Prediction, CalibrationData


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "ph", "tds", "temperature", "turbidity", "source_device_id")
    list_filter = ("timestamp",)
    search_fields = ("source_device_id",)
    date_hierarchy = "timestamp"
    list_per_page = 50


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "reading", "timestamp", "authenticity_status", "confidence")
    list_filter = ("authenticity_status", "timestamp")
    date_hierarchy = "timestamp"
    raw_id_fields = ("reading",)
    list_per_page = 50


@admin.register(CalibrationData)
class CalibrationDataAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "run_id")
    list_filter = ("timestamp",)
    date_hierarchy = "timestamp"
    list_per_page = 50
