"""
websocket_server/routing.py
T4.2 ✅  WebSocket URL routing.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Public
    re_path(r"^ws/market/ticker/(?P<symbol>[A-Z]+)/$",                consumers.MarketTickerConsumer.as_asgi()),
    re_path(r"^ws/market/ohlcv/(?P<symbol>[A-Z]+)/(?P<timeframe>\w+)/$", consumers.MarketOHLCVConsumer.as_asgi()),
    # Private
    re_path(r"^ws/portfolio/$",     consumers.PortfolioConsumer.as_asgi()),
    re_path(r"^ws/orders/$",        consumers.OrderConsumer.as_asgi()),
    re_path(r"^ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r"^ws/scanner/$",       consumers.ScannerConsumer.as_asgi()),
    re_path(r"^ws/ai/$",            consumers.AIRecommendationConsumer.as_asgi()),
]
