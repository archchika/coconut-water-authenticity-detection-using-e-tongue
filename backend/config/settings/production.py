"""
Phase 5.3 / 6.8 — Django production settings.

Load from base; override DEBUG, ALLOWED_HOSTS, DATABASES (PostgreSQL), SECRET_KEY.
Set DJANGO_SETTINGS_MODULE=config.settings.production and provide env vars (see .env.example).
Phase 6.8: HTTPS, CORS whitelist, secure cookies, rate limiting on upload.
"""
import os

from . import base as _base
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",") or ["*"]

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production")

# PostgreSQL (Phase 5.4)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "etongue"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# CORS: restrict in production (Phase 6.8)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") or []

# Secure cookies and HTTPS (Phase 6.8)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Set SECURE_SSL_REDIRECT = True if the reverse proxy does not force HTTPS
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in ("true", "1", "yes")

# Rate limiting on upload (Phase 6.8): throttle scope "upload" applied on UploadDataView
REST_FRAMEWORK = {
    **_base.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "upload": os.environ.get("UPLOAD_THROTTLE_RATE", "60/hour"),
    },
}

STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
