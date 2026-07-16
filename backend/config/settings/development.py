"""
TradeMind AI - Development Settings
=====================================
Inherit all base settings and override for local development.
Usage:
    export DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS, MIDDLEWARE, LOGGING

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
]

# ---------------------------------------------------------------------------
# Database (can still be overridden via .env)
# ---------------------------------------------------------------------------
# Inherits PostgreSQL config from base.py.
# Developers can point DB_HOST=localhost in their .env.

# ---------------------------------------------------------------------------
# Email — print to console
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# CORS — relaxed for local dev
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True  # Overrides CORS_ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Django Debug Toolbar (optional, installed only if present)
# ---------------------------------------------------------------------------
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1"]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    }
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Caching — use local-memory cache so dev works without Redis
# (swap to RedisCache if you have Redis running locally)
# ---------------------------------------------------------------------------
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "trademind-dev",
#     }
# }

# ---------------------------------------------------------------------------
# Celery — run tasks eagerly in development (no broker needed)
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Logging — verbose, coloured output
# ---------------------------------------------------------------------------
LOGGING["handlers"]["console"]["formatter"] = "verbose"  # type: ignore[index]
LOGGING["root"]["level"] = "DEBUG"  # type: ignore[index]
LOGGING["loggers"]["trademind"]["level"] = "DEBUG"  # type: ignore[index]
LOGGING["loggers"]["django"]["level"] = "INFO"  # type: ignore[index]

# ---------------------------------------------------------------------------
# Static files — Django serves them in dev
# ---------------------------------------------------------------------------
# No changes needed; Django dev server serves STATIC_URL automatically.

# ---------------------------------------------------------------------------
# Security — relaxed for dev
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ---------------------------------------------------------------------------
# Developer conveniences
# ---------------------------------------------------------------------------
SHELL_PLUS = "ipython"  # django-extensions shell_plus uses IPython if installed
SHELL_PLUS_PRINT_SQL = True
