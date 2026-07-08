from django.urls import path
from .views import ReportListView, ReportGenerateView, ReportDetailView

urlpatterns = [
    path("",           ReportListView.as_view(),     name="report-list"),
    path("generate/",  ReportGenerateView.as_view(), name="report-generate"),
    path("<str:pk>/",  ReportDetailView.as_view(),   name="report-detail"),
]
