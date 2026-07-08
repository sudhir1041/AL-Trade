from django.urls import path
from .views import (
    StrategyLibraryView, UserStrategyListCreateView, UserStrategyDetailView,
    StrategyActivateView, StrategyDeactivateView,
    StrategyPerformanceView, StrategyBacktestView,
)

urlpatterns = [
    path("library/",                       StrategyLibraryView.as_view(),          name="strategy-library"),
    path("",                               UserStrategyListCreateView.as_view(),   name="strategy-list"),
    path("<str:pk>/",                      UserStrategyDetailView.as_view(),       name="strategy-detail"),
    path("<str:pk>/activate/",             StrategyActivateView.as_view(),         name="strategy-activate"),
    path("<str:pk>/deactivate/",           StrategyDeactivateView.as_view(),       name="strategy-deactivate"),
    path("<str:pk>/performance/",          StrategyPerformanceView.as_view(),      name="strategy-performance"),
    path("<str:pk>/backtest/",             StrategyBacktestView.as_view(),         name="strategy-backtest"),
]
