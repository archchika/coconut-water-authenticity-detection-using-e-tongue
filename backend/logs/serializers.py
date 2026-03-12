"""
Phase 6.6 — List serializer for SystemLog API.
"""
from rest_framework import serializers
from .models import SystemLog


class SystemLogListSerializer(serializers.ModelSerializer):
    """List output for GET /api/logs/."""

    class Meta:
        model = SystemLog
        fields = ("id", "timestamp", "level", "component", "message", "metadata")
