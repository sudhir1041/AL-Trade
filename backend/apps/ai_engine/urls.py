from django.urls import path
from .views import (
    AIAnalyzeView, AIScoreView, AIRecommendationView,
    AIExplanationView, AIHistoryView,
)

urlpatterns = [
    path("analyze/",                  AIAnalyzeView.as_view(),        name="ai-analyze"),
    path("score/<str:symbol>/",       AIScoreView.as_view(),          name="ai-score"),
    path("recommendation/<str:symbol>/", AIRecommendationView.as_view(), name="ai-recommendation"),
    path("explanation/<str:symbol>/", AIExplanationView.as_view(),    name="ai-explanation"),
    path("history/",                  AIHistoryView.as_view(),        name="ai-history"),
]
