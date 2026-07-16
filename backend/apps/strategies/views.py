"""
apps/strategies/views.py
------------------------
T9 ✅  Strategy Engine REST endpoints (Vol.5 §11).

GET    /strategies/            – browse strategy library
POST   /strategies/            – create user strategy config
GET    /strategies/{id}/       – user strategy detail
PATCH  /strategies/{id}/       – update config
DELETE /strategies/{id}/       – remove
POST   /strategies/{id}/activate/
POST   /strategies/{id}/deactivate/
GET    /strategies/{id}/performance/
POST   /strategies/{id}/backtest/
"""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import (
    created_response, error_response, no_content_response, success_response
)
from .models import Strategy, UserStrategy, StrategyPerformance, BacktestJob
from .serializers import (
    StrategySerializer, UserStrategySerializer,
    StrategyPerformanceSerializer, BacktestJobSerializer,
)

logger = logging.getLogger("trademind.strategies.views")


class StrategyLibraryView(APIView):
    """GET /api/v1/strategies/library/ — platform strategy catalogue"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = Strategy.objects.filter(is_active=True).order_by("sort_order", "name")
        return success_response(data=StrategySerializer(qs, many=True).data)


class UserStrategyListCreateView(APIView):
    """GET/POST /api/v1/strategies/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = UserStrategy.objects.filter(
            user=request.user, deleted_at__isnull=True
        ).select_related("strategy").order_by("-created_at")
        return success_response(
            data=UserStrategySerializer(qs, many=True).data,
            meta={"count": qs.count()},
        )

    def post(self, request: Request):
        serializer = UserStrategySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid strategy config.",
                                   details={"field_errors": serializer.errors})
        us = serializer.save(
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            created_by=request.user.id,
        )
        logger.info("UserStrategy created: %s user=%s", us.name, request.user.id)
        return created_response(
            data=UserStrategySerializer(us).data,
            message=f"Strategy '{us.name}' configured.",
        )


class UserStrategyDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/strategies/{id}/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return UserStrategy.objects.get(pk=pk, user=user, deleted_at__isnull=True)
        except UserStrategy.DoesNotExist:
            return None

    def get(self, request: Request, pk: str):
        us = self._get(pk, request.user)
        if not us:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)
        return success_response(data=UserStrategySerializer(us).data)

    def patch(self, request: Request, pk: str):
        us = self._get(pk, request.user)
        if not us:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)
        serializer = UserStrategySerializer(us, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid update.", details=serializer.errors)
        serializer.save(updated_by=request.user.id)
        return success_response(data=serializer.data, message="Strategy updated.")

    def delete(self, request: Request, pk: str):
        us = self._get(pk, request.user)
        if not us:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)
        us.soft_delete(deleted_by=request.user.id)
        return no_content_response("Strategy removed.")


class StrategyActivateView(APIView):
    """POST /api/v1/strategies/{id}/activate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            us = UserStrategy.objects.get(pk=pk, user=request.user)
        except UserStrategy.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)
        us.is_active = True
        us.save(update_fields=["is_active"])
        return success_response(message=f"Strategy '{us.name}' activated.")


class StrategyDeactivateView(APIView):
    """POST /api/v1/strategies/{id}/deactivate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            us = UserStrategy.objects.get(pk=pk, user=request.user)
        except UserStrategy.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)
        us.is_active = False
        us.save(update_fields=["is_active"])
        return success_response(message=f"Strategy '{us.name}' deactivated.")


class StrategyPerformanceView(APIView):
    """GET /api/v1/strategies/{id}/performance/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str):
        try:
            us   = UserStrategy.objects.get(pk=pk, user=request.user)
            perf = StrategyPerformance.objects.get(user_strategy=us)
        except (UserStrategy.DoesNotExist, StrategyPerformance.DoesNotExist):
            return error_response("RESOURCE_NOT_FOUND",
                                   "No performance data yet.", status_code=404)
        return success_response(data=StrategyPerformanceSerializer(perf).data)


class StrategyBacktestView(APIView):
    """POST /api/v1/strategies/{id}/backtest/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            us = UserStrategy.objects.get(pk=pk, user=request.user)
        except UserStrategy.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Strategy not found.", status_code=404)

        from apps.market.models import TradingPair
        symbol = request.data.get("symbol", "BTCUSDT")
        pair   = TradingPair.objects.filter(symbol=symbol.upper()).first()
        if not pair:
            return error_response("RESOURCE_NOT_FOUND", f"Symbol {symbol} not found.")

        serializer = BacktestJobSerializer(data={
            **request.data,
            "strategy":    str(us.strategy_id),
            "trading_pair": str(pair.id),
        })
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid backtest params.",
                                   details=serializer.errors)
        job = serializer.save(
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            strategy=us.strategy,
            trading_pair=pair,
        )
        from apps.strategies.tasks import run_backtest
        run_backtest.delay(str(job.id))
        return created_response(
            data=BacktestJobSerializer(job).data,
            message="Backtest queued.",
        )
