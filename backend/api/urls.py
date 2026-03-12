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
    WeeklyAggregationView,
    MonthlyAggregationView,
    SensorReadingListView,
    PredictionListView,
)
from alerts.views import AlertListView, AlertResolveView
from logs.views import SystemLogListView

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("upload-data/", UploadDataView.as_view(), name="upload-data"),
    path("daily/", DailyAggregationView.as_view(), name="daily"),
    path("weekly/", WeeklyAggregationView.as_view(), name="weekly"),
    path("monthly/", MonthlyAggregationView.as_view(), name="monthly"),
    path("readings/", SensorReadingListView.as_view(), name="readings-list"),
    path("predictions/", PredictionListView.as_view(), name="predictions-list"),
    path("alerts/", AlertListView.as_view(), name="alerts-list"),
    path("alerts/<int:pk>/", AlertResolveView.as_view(), name="alert-resolve"),
    path("logs/", SystemLogListView.as_view(), name="logs-list"),
]
