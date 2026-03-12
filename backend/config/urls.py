"""
Phase 5.3 — Root URL configuration.
API routes are mounted under /api/ (see api.urls).
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
