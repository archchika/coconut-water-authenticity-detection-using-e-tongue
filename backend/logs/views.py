"""
Phase 6.6 — SystemLog list API with search/filter (auth required).
"""
from datetime import datetime, timezone as dt_timezone

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import SystemLog
from .serializers import SystemLogListSerializer


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


class SystemLogListView(APIView):
    """GET /api/logs/?date_from=&date_to=&level=&component=&search=&limit= (Phase 6.6). Auth required."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SystemLog.objects.all().order_by("-timestamp")
        start, end = _parse_date_range(request)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        level = request.query_params.get("level")
        if level:
            qs = qs.filter(level=level)
        component = request.query_params.get("component")
        if component:
            qs = qs.filter(component__icontains=component)
        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(message__icontains=search)
        limit = min(int(request.query_params.get("limit", 50)), 500)
        qs = qs[:limit]
        serializer = SystemLogListSerializer(qs, many=True)
        return Response(serializer.data)
