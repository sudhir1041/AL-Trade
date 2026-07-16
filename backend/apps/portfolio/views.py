"""
apps/portfolio/views.py
T12 ✅  Portfolio Management REST endpoints (Vol.5 §14).
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from core.responses import error_response, success_response
from .models import Portfolio, PnLHistory, PortfolioHistory
from .serializers import (
    PortfolioSerializer, PnLHistorySerializer, PortfolioHistorySerializer
)


class PortfolioView(APIView):
    """GET /api/v1/portfolio/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        portfolios = (
            Portfolio.objects.filter(user=request.user)
            .select_related("exchange_account__exchange")
            .prefetch_related("assets")
        )
        return success_response(
            data=PortfolioSerializer(portfolios, many=True).data,
            meta={"count": portfolios.count()},
        )


class PortfolioPerformanceView(APIView):
    """GET /api/v1/portfolio/performance/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        limit  = int(request.query_params.get("limit", 90))
        pnl_qs = (
            PnLHistory.objects.filter(user=request.user)
            .order_by("-date")[:limit]
        )
        return success_response(data=PnLHistorySerializer(reversed(list(pnl_qs)), many=True).data)


class PortfolioHistoryView(APIView):
    """GET /api/v1/portfolio/history/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        limit  = int(request.query_params.get("limit", 168))  # 7 days hourly
        portfolios = Portfolio.objects.filter(user=request.user).values_list("id", flat=True)
        history = (
            PortfolioHistory.objects.filter(portfolio_id__in=portfolios)
            .order_by("-recorded_at")[:limit]
        )
        return success_response(data=PortfolioHistorySerializer(reversed(list(history)), many=True).data)


class PortfolioPnLView(APIView):
    """GET /api/v1/portfolio/pnl/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from django.db.models import Sum
        agg = PnLHistory.objects.filter(user=request.user).aggregate(
            total_pnl=Sum("daily_pnl"),
            total_trades=Sum("trade_count"),
            total_wins=Sum("win_count"),
            total_losses=Sum("loss_count"),
        )
        total_trades = agg["total_trades"] or 0
        total_wins   = agg["total_wins"] or 0
        win_rate     = (total_wins / total_trades * 100) if total_trades > 0 else 0

        return success_response(data={
            "total_realized_pnl": str(agg["total_pnl"] or 0),
            "total_trades":       total_trades,
            "total_wins":         total_wins,
            "total_losses":       agg["total_losses"] or 0,
            "overall_win_rate":   round(win_rate, 2),
        })
