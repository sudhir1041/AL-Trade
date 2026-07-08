from django.urls import path
from .views import (
    ScannerRunView, ScannerStatusView, ScannerResultsView,
    ScannerCandidatesView, ScannerSettingsView,
)

urlpatterns = [
    path("run/",        ScannerRunView.as_view(),        name="scanner-run"),
    path("status/",     ScannerStatusView.as_view(),     name="scanner-status"),
    path("results/",    ScannerResultsView.as_view(),    name="scanner-results"),
    path("candidates/", ScannerCandidatesView.as_view(), name="scanner-candidates"),
    path("settings/",   ScannerSettingsView.as_view(),   name="scanner-settings"),
]
