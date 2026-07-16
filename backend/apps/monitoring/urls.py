from django.urls import path
from .views import HealthCheckView, MetricsView

urlpatterns = [
    path("health/",  HealthCheckView.as_view(), name="health"),
    path("metrics/", MetricsView.as_view(),     name="metrics"),
]
