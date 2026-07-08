from django.urls import path
from .views import (
    MarketListView, MarketDetailView, MarketTickerView,
    MarketOHLCVView, MarketFundingRateView, MarketOpenInterestView,
    MarketSearchView,
)

urlpatterns = [
    path("",                               MarketListView.as_view(),         name="market-list"),
    path("search/",                        MarketSearchView.as_view(),       name="market-search"),
    path("<str:symbol>/",                  MarketDetailView.as_view(),       name="market-detail"),
    path("<str:symbol>/ticker/",           MarketTickerView.as_view(),       name="market-ticker"),
    path("<str:symbol>/ohlcv/",            MarketOHLCVView.as_view(),        name="market-ohlcv"),
    path("<str:symbol>/funding-rate/",     MarketFundingRateView.as_view(),  name="market-funding"),
    path("<str:symbol>/open-interest/",    MarketOpenInterestView.as_view(), name="market-oi"),
]
