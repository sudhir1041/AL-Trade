from django.urls import path
from .views import (
    RiskProfileView, RiskExposureView,
    RiskLimitsView, EmergencyStopView, RiskResumeView,
)

urlpatterns = [
    path("profile/",         RiskProfileView.as_view(),    name="risk-profile"),
    path("exposure/",        RiskExposureView.as_view(),   name="risk-exposure"),
    path("limits/",          RiskLimitsView.as_view(),     name="risk-limits"),
    path("emergency-stop/",  EmergencyStopView.as_view(),  name="risk-emergency-stop"),
    path("resume/",          RiskResumeView.as_view(),     name="risk-resume"),
]
