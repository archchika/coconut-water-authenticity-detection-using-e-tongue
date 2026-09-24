"""
Phase 5.3 / 5.5 / 5.6 / 5.7 / 6.5 / 6.6 — API URL routing.

POST /api/upload-data/ (5.5, auth); GET /api/daily/, weekly/, monthly/ (5.6, public).
POST /api/auth/token/ (5.7); GET /api/readings/, /api/predictions/ (6.5, auth).
GET /api/alerts/, PATCH /api/alerts/<id>/ (6.6, auth); GET /api/logs/ (6.6, auth).
"""
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from readings.views import (
    UploadDataView,
    DailyAggregationView,
    DailyReadingsListView,
    ValidationSummaryView,
    WeeklyAggregationView,
    MonthlyAggregationView,
    SensorReadingListView,
    PredictionListView,
    PredictCompositionView,
    PredictBatchView,
    Esp32ReadingView,
    Esp32RobotStatusView,
    Esp32LiveView,
)
from alerts.views import AlertListView, AlertResolveView
from logs.views import SystemLogListView

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("upload-data/", UploadDataView.as_view(), name="upload-data"),
    path("daily/", DailyAggregationView.as_view(), name="daily"),
    path("daily/readings/", DailyReadingsListView.as_view(), name="daily-readings"),
    path("validation/summary/", ValidationSummaryView.as_view(), name="validation-summary"),
    path("weekly/", WeeklyAggregationView.as_view(), name="weekly"),
    path("monthly/", MonthlyAggregationView.as_view(), name="monthly"),
    path("predict/", PredictCompositionView.as_view(), name="predict-composition"),
    path("predict-batch/", PredictBatchView.as_view(), name="predict-batch"),
    path("esp32-reading/", Esp32ReadingView.as_view(), name="esp32-reading"),
    path("esp32-status/", Esp32RobotStatusView.as_view(), name="esp32-status"),
    path("esp32-live/", Esp32LiveView.as_view(), name="esp32-live"),
    path("readings/", SensorReadingListView.as_view(), name="readings-list"),
    path("predictions/", PredictionListView.as_view(), name="predictions-list"),
    path("alerts/", AlertListView.as_view(), name="alerts-list"),
    path("alerts/<int:pk>/", AlertResolveView.as_view(), name="alert-resolve"),
    path("logs/", SystemLogListView.as_view(), name="logs-list"),
]
