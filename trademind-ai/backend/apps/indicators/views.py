"""
apps/indicators/views.py
-------------------------
T6 ✅  Technical analysis API endpoints.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from core.responses import error_response, success_response
from .engine import IndicatorEngine


class IndicatorView(APIView):
    """GET /api/v1/indicators/{symbol}/?timeframe=1h"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1h")
        engine    = IndicatorEngine()
        data      = engine.compute_all(symbol.upper(), timeframe)
        if not data:
            return error_response("RESOURCE_NOT_FOUND",
                                   f"No indicator data for {symbol} {timeframe}.", status_code=404)
        return success_response(data=data, meta={"symbol": symbol.upper(), "timeframe": timeframe})


class IndicatorRSIView(APIView):
    """GET /api/v1/indicators/{symbol}/rsi/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1h")
        engine    = IndicatorEngine()
        data      = engine.compute_all(symbol.upper(), timeframe)
        return success_response(data={k: v for k, v in data.items() if "rsi" in k})


class IndicatorMACDView(APIView):
    """GET /api/v1/indicators/{symbol}/macd/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1h")
        engine    = IndicatorEngine()
        data      = engine.compute_all(symbol.upper(), timeframe)
        return success_response(data={k: v for k, v in data.items() if "macd" in k})
