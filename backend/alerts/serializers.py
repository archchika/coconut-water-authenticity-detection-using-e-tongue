"""
Phase 6.6 — List and update serializers for Alert API.
"""
from rest_framework import serializers
from .models import Alert


class AlertListSerializer(serializers.ModelSerializer):
    """List output for GET /api/alerts/. 'reading' is the SensorReading id (nullable)."""

    class Meta:
        model = Alert
        fields = ("id", "timestamp", "type", "message", "reading", "resolved")


class AlertResolveSerializer(serializers.Serializer):
    """Body for PATCH resolve: { \"resolved\": true|false }."""

    resolved = serializers.BooleanField(required=True)
