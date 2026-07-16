from django.urls import path
from .views import IndicatorView, IndicatorRSIView, IndicatorMACDView

urlpatterns = [
    path("<str:symbol>/",      IndicatorView.as_view(),     name="indicators-all"),
    path("<str:symbol>/rsi/",  IndicatorRSIView.as_view(),  name="indicators-rsi"),
    path("<str:symbol>/macd/", IndicatorMACDView.as_view(), name="indicators-macd"),
]
