"""
apps/monitoring/views.py
T1.4 ✅  Health check + Prometheus metrics endpoint.
"""
import time
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """GET /api/v1/monitoring/health/"""
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {}

        # Database
        try:
            from django.db import connection
            connection.ensure_connection()
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"

        # Redis
        try:
            from django.core.cache import cache
            cache.set("health_check", "1", timeout=5)
            checks["redis"] = "ok" if cache.get("health_check") == "1" else "error"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        # Celery
        try:
            from config.celery import app
            app.control.inspect(timeout=1).ping()
            checks["celery"] = "ok"
        except Exception:
            checks["celery"] = "unreachable"

        all_ok = all(v == "ok" for v in checks.values())
        return JsonResponse({
            "status":    "healthy" if all_ok else "degraded",
            "timestamp": time.time(),
            "checks":    checks,
        }, status=200 if all_ok else 503)


class MetricsView(APIView):
    """GET /api/v1/monitoring/metrics/  — Prometheus metrics"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
        except ImportError:
            return HttpResponse("# prometheus_client not installed\n",
                                content_type="text/plain")
