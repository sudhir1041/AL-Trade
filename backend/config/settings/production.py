"""
TradeMind AI - Production Settings
=====================================
Inherit all base settings and harden for production deployment.
Usage:
    export DJANGO_SETTINGS_MODULE=config.settings.production

All sensitive values MUST be supplied via environment variables.
No secrets should be committed to source control.
"""

import os

from .base import *  # noqa: F401, F403
from .base import LOGGING, CACHES

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

# ---------------------------------------------------------------------------
# Security — HTTPS enforcement
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS — tell browsers to only use HTTPS for 1 year, including subdomains
SECURE_HSTS_SECONDS = 31_536_000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 1_209_600            # 2 weeks

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Misc security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ---------------------------------------------------------------------------
# Email — SMTP
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ---------------------------------------------------------------------------
# Caching — enforce Redis with connection pooling
# ---------------------------------------------------------------------------
CACHES["default"]["OPTIONS"] = {  # type: ignore[index]
    **CACHES["default"].get("OPTIONS", {}),  # type: ignore[index]
    "IGNORE_EXCEPTIONS": False,   # Surface cache errors in production
    "CONNECTION_POOL_KWARGS": {
        "max_connections": int(os.environ.get("REDIS_MAX_CONNECTIONS", "50")),
    },
}

# ---------------------------------------------------------------------------
# Static files — served via WhiteNoise / CDN in production
# ---------------------------------------------------------------------------
try:
    import whitenoise  # noqa: F401
    from .base import MIDDLEWARE  # noqa: F811
    # Insert WhiteNoise after SecurityMiddleware
    _idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE = (
        MIDDLEWARE[: _idx + 1]
        + ["whitenoise.middleware.WhiteNoiseMiddleware"]
        + MIDDLEWARE[_idx + 1 :]
    )
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
except (ImportError, ValueError):
    pass

# ---------------------------------------------------------------------------
# Logging — structured JSON to stdout (consumed by log aggregator)
# ---------------------------------------------------------------------------
LOGGING["handlers"]["console"]["formatter"] = "json"  # type: ignore[index]
LOGGING["root"]["level"] = os.environ.get("LOG_LEVEL", "WARNING")  # type: ignore[index]

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------
# Enable persistent connections to the database
CONN_MAX_AGE = int(os.environ.get("DB_CONN_MAX_AGE", "60"))

# ---------------------------------------------------------------------------
# Admin hardening
# ---------------------------------------------------------------------------
# Randomize the admin URL to reduce attack surface
ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "admin/")

# ---------------------------------------------------------------------------
# Celery — never run eagerly in production
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
