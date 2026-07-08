"""
apps/market/views.py
--------------------
Market data API endpoints (Vol.5 §7).

GET /markets/                     – list all active trading pairs
GET /markets/{symbol}/            – pair detail
GET /markets/{symbol}/ticker/     – live ticker
GET /markets/{symbol}/ohlcv/      – candlestick data (?timeframe=1h&limit=200)
GET /markets/{symbol}/funding-rate/
GET /markets/{symbol}/open-interest/
GET /markets/search/              – search pairs by symbol
"""

import logging

from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import error_response, success_response
from .models import FundingRate, OHLCV, OpenInterest, Ticker, TradingPair
from .serializers import (
    FundingRateSerializer, OHLCVSerializer,
    OpenInterestSerializer, TickerSerializer, TradingPairSerializer,
)

logger = logging.getLogger("trademind.market")

CACHE_TTL = 5   # seconds — market data refreshes every 5s


class MarketListView(APIView):
    """GET /api/v1/markets/  — T4.1 ✅"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        exchange = request.query_params.get("exchange")
        qs = TradingPair.objects.filter(is_active=True).select_related("exchange")
        if exchange:
            qs = qs.filter(exchange__slug=exchange)
        return success_response(
            data=TradingPairSerializer(qs, many=True).data,
            meta={"count": qs.count()},
        )


class MarketDetailView(APIView):
    """GET /api/v1/markets/{symbol}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        qs = TradingPair.objects.filter(symbol=symbol.upper(), is_active=True)
        if not qs.exists():
            return error_response("RESOURCE_NOT_FOUND", f"Symbol {symbol} not found.", status_code=404)
        return success_response(data=TradingPairSerializer(qs.first()).data)


class MarketTickerView(APIView):
    """GET /api/v1/markets/{symbol}/ticker/  — T4.1 ✅ (Redis cached)"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        cache_key = f"ticker:{symbol.upper()}"
        cached    = cache.get(cache_key)
        if cached:
            return success_response(data=cached)

        ticker = (
            Ticker.objects.filter(trading_pair__symbol=symbol.upper())
            .select_related("trading_pair")
            .order_by("-timestamp")
            .first()
        )
        if not ticker:
            return error_response("RESOURCE_NOT_FOUND", f"No ticker data for {symbol}.", status_code=404)

        data = TickerSerializer(ticker).data
        cache.set(cache_key, data, timeout=CACHE_TTL)
        return success_response(data=data)


class MarketOHLCVView(APIView):
    """GET /api/v1/markets/{symbol}/ohlcv/?timeframe=1h&limit=200  — T4.1 ✅"""
    permission_classes = [IsAuthenticated]

    VALID_TIMEFRAMES = {"1m", "5m", "15m", "1h", "4h", "1d"}

    def get(self, request: Request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1h")
        limit     = min(int(request.query_params.get("limit", 200)), 1000)

        if timeframe not in self.VALID_TIMEFRAMES:
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid timeframe. Valid: {', '.join(sorted(self.VALID_TIMEFRAMES))}",
            )

        pair = TradingPair.objects.filter(symbol=symbol.upper()).first()
        if not pair:
            return error_response("RESOURCE_NOT_FOUND", f"Symbol {symbol} not found.", status_code=404)

        candles = (
            OHLCV.objects.filter(trading_pair=pair, timeframe=timeframe)
            .order_by("-timestamp")[:limit]
        )
        return success_response(
            data=OHLCVSerializer(reversed(list(candles)), many=True).data,
            meta={"symbol": symbol.upper(), "timeframe": timeframe, "count": len(candles)},
        )


class MarketFundingRateView(APIView):
    """GET /api/v1/markets/{symbol}/funding-rate/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        pair = TradingPair.objects.filter(symbol=symbol.upper(), is_futures=True).first()
        if not pair:
            return error_response("RESOURCE_NOT_FOUND", f"No futures pair found for {symbol}.", status_code=404)
        rate = FundingRate.objects.filter(trading_pair=pair).order_by("-timestamp").first()
        if not rate:
            return error_response("RESOURCE_NOT_FOUND", "No funding rate data available.", status_code=404)
        return success_response(data=FundingRateSerializer(rate).data)


class MarketOpenInterestView(APIView):
    """GET /api/v1/markets/{symbol}/open-interest/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        pair = TradingPair.objects.filter(symbol=symbol.upper(), is_futures=True).first()
        if not pair:
            return error_response("RESOURCE_NOT_FOUND", f"No futures pair found for {symbol}.", status_code=404)
        oi = OpenInterest.objects.filter(trading_pair=pair).order_by("-timestamp").first()
        if not oi:
            return error_response("RESOURCE_NOT_FOUND", "No open interest data available.", status_code=404)
        return success_response(data=OpenInterestSerializer(oi).data)


class MarketSearchView(APIView):
    """GET /api/v1/markets/search/?q=BTC"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        q = request.query_params.get("q", "").strip().upper()
        if len(q) < 2:
            return error_response("VALIDATION_ERROR", "Search query must be at least 2 characters.")
        qs = TradingPair.objects.filter(symbol__icontains=q, is_active=True)[:20]
        return success_response(data=TradingPairSerializer(qs, many=True).data)
