from django.urls import path
from .views import PortfolioView, PortfolioPerformanceView, PortfolioHistoryView, PortfolioPnLView

urlpatterns = [
    path("",             PortfolioView.as_view(),            name="portfolio"),
    path("performance/", PortfolioPerformanceView.as_view(), name="portfolio-performance"),
    path("history/",     PortfolioHistoryView.as_view(),     name="portfolio-history"),
    path("pnl/",         PortfolioPnLView.as_view(),         name="portfolio-pnl"),
]
