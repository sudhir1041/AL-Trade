"""
config/urls.py
--------------
Main URL configuration for TradeMind AI.
All API endpoints are prefixed with /api/v1/
"""

from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health_check(request):
    """GET /health/ — simple health check for load balancers."""
    return JsonResponse({"status": "ok", "service": "TradeMind AI API"})


urlpatterns = [
    # Django admin
    path("django-admin/", admin.site.urls),

    # Health check
    path("health/", health_check, name="health-check"),

    # API v1
    path("api/v1/auth/",          include("apps.accounts.urls")),
    path("api/v1/users/",         include("apps.users.urls")),
    path("api/v1/exchanges/",     include("apps.exchanges.urls")),
    path("api/v1/markets/",       include("apps.market.urls")),
    path("api/v1/scanner/",       include("apps.scanner.urls")),
    path("api/v1/indicators/",    include("apps.indicators.urls")),
    path("api/v1/ai/",            include("apps.ai_engine.urls")),
    path("api/v1/strategies/",    include("apps.strategies.urls")),
    path("api/v1/risk/",          include("apps.risk.urls")),
    path("api/v1/orders/",        include("apps.orders.urls")),
    path("api/v1/portfolio/",     include("apps.portfolio.urls")),
    path("api/v1/reports/",       include("apps.reports.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/paper/",         include("apps.strategies.paper_urls")),
    path("api/v1/backtest/",      include("apps.strategies.backtest_urls")),
    path("api/v1/billing/",       include("apps.billing.urls")),
    path("api/v1/admin/",         include("apps.admin_panel.urls")),
    path("api/v1/monitoring/",    include("apps.monitoring.urls")),
]
