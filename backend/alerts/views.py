"""
Phase 6.6 — Alert list and resolve API (auth required).
"""
from datetime import datetime, timezone as dt_timezone

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Alert
from .serializers import AlertListSerializer, AlertResolveSerializer


def _parse_date_range(request):
    """Parse optional date_from, date_to (YYYY-MM-DD). Returns (start, end) or (None, None)."""
    start = end = None
    if request.query_params.get("date_from"):
        try:
            start = timezone.make_aware(
                datetime.strptime(request.query_params["date_from"], "%Y-%m-%d"),
                timezone=dt_timezone.utc,
            )
        except ValueError:
            pass
    if request.query_params.get("date_to"):
        try:
            end = timezone.make_aware(
                datetime.strptime(request.query_params["date_to"], "%Y-%m-%d"),
                timezone=dt_timezone.utc,
            )
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            pass
    return start, end


class AlertListView(APIView):
    """GET /api/alerts/?date_from=&date_to=&type=&resolved=&limit= (Phase 6.6). Auth required."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Alert.objects.all().order_by("-timestamp")
        start, end = _parse_date_range(request)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        type_val = request.query_params.get("type")
        if type_val:
            qs = qs.filter(type=type_val)
        resolved_val = request.query_params.get("resolved")
        if resolved_val is not None and resolved_val != "":
            qs = qs.filter(resolved=resolved_val.lower() in ("true", "1", "yes"))
        limit = min(int(request.query_params.get("limit", 50)), 500)
        qs = qs[:limit]
        serializer = AlertListSerializer(qs, many=True)
        return Response(serializer.data)


class AlertResolveView(APIView):
    """PATCH /api/alerts/<id>/ — set resolved=true|false (Phase 6.6). Auth required."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlertResolveSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        alert.resolved = serializer.validated_data["resolved"]
        alert.save(update_fields=["resolved"])
        return Response(AlertListSerializer(alert).data)
