"""
apps/ai_engine/views.py
-----------------------
T7 ✅  AI Decision Engine REST endpoints (Vol.5 §10).

POST /ai/analyze/                – trigger scoring for a symbol
GET  /ai/score/{symbol}/         – latest score for a symbol
GET  /ai/recommendation/{symbol}/– latest recommendation
GET  /ai/explanation/{symbol}/   – explanation of last recommendation
GET  /ai/history/                – user's AI recommendation history
"""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import error_response, success_response
from .models import AIScore, MarketRegimeSnapshot
from .serializers import AIScoreSerializer, MarketRegimeSerializer

logger = logging.getLogger("trademind.ai_engine.views")


class AIAnalyzeView(APIView):
    """POST /api/v1/ai/analyze/  — trigger on-demand AI scoring"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        symbol = request.data.get("symbol", "").upper().strip()
        if not symbol:
            return error_response("VALIDATION_ERROR", "symbol is required.")

        from apps.market.models import TradingPair
        pair = TradingPair.objects.filter(symbol=symbol, is_active=True).first()
        if not pair:
            return error_response("RESOURCE_NOT_FOUND", f"Symbol {symbol} not found.", status_code=404)

        from apps.ai_engine.tasks import run_ai_scoring
        run_ai_scoring.delay(pair_id=str(pair.id), scanner_factors={})

        return success_response(
            data={"symbol": symbol, "status": "queued"},
            message=f"AI scoring queued for {symbol}. Results available shortly.",
        )


class AIScoreView(APIView):
    """GET /api/v1/ai/score/{symbol}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        score = (
            AIScore.objects.filter(trading_pair__symbol=symbol.upper())
            .order_by("-created_at")
            .first()
        )
        if not score:
            return error_response("RESOURCE_NOT_FOUND",
                                   f"No AI score found for {symbol}.", status_code=404)
        return success_response(data=AIScoreSerializer(score).data)


class AIRecommendationView(APIView):
    """GET /api/v1/ai/recommendation/{symbol}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        score = (
            AIScore.objects.filter(
                trading_pair__symbol=symbol.upper(),
                direction__in=["BUY", "SELL", "HOLD"],
            )
            .order_by("-created_at")
            .first()
        )
        if not score:
            return error_response("RESOURCE_NOT_FOUND",
                                   f"No recommendation found for {symbol}.", status_code=404)
        return success_response(data={
            "symbol":             symbol.upper(),
            "direction":          score.direction,
            "confidence":         str(score.confidence_score),
            "risk_level":         score.risk_level,
            "entry_zone":         {"low": str(score.entry_zone_low), "high": str(score.entry_zone_high)},
            "stop_loss":          str(score.stop_loss_suggest),
            "take_profit_1":      str(score.tp1_suggest),
            "take_profit_2":      str(score.tp2_suggest),
            "risk_reward":        str(score.risk_reward_ratio),
            "compatible_strategies": score.compatible_strategies,
            "timestamp":          score.created_at.isoformat(),
        })


class AIExplanationView(APIView):
    """GET /api/v1/ai/explanation/{symbol}/  — explainable AI output"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, symbol: str):
        score = (
            AIScore.objects.filter(trading_pair__symbol=symbol.upper())
            .order_by("-created_at")
            .first()
        )
        if not score:
            return error_response("RESOURCE_NOT_FOUND",
                                   f"No AI data found for {symbol}.", status_code=404)
        return success_response(data={
            "symbol":              symbol.upper(),
            "reasoning":           score.reasoning,
            "supporting_factors":  score.supporting_factors,
            "conflicting_factors": score.conflicting_factors,
            "mtf_alignment":       score.mtf_alignment,
            "market_regime":       score.market_regime,
            "confidence":          str(score.confidence_score),
            "generated_at":        score.created_at.isoformat(),
        })


class AIHistoryView(APIView):
    """GET /api/v1/ai/history/?symbol=BTCUSDT&limit=50"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        symbol = request.query_params.get("symbol", "").upper()
        limit  = min(int(request.query_params.get("limit", 50)), 200)
        qs     = AIScore.objects.select_related("trading_pair").order_by("-created_at")
        if symbol:
            qs = qs.filter(trading_pair__symbol=symbol)
        qs = qs[:limit]
        return success_response(
            data=AIScoreSerializer(qs, many=True).data,
            meta={"count": len(qs)},
        )
