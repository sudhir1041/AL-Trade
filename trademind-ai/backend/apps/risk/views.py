"""
apps/risk/views.py
------------------
T10 ✅  Risk Management REST endpoints (Vol.5 §12).

GET  /risk/profile/         – get active risk profile
PATCH /risk/profile/        – update risk profile
GET  /risk/exposure/        – current portfolio exposure
GET  /risk/limits/          – current limits and usage
POST /risk/emergency-stop/  – trigger emergency stop
POST /risk/resume/          – resume after emergency stop
"""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import error_response, success_response
from .models import DailyLossTracker, EmergencyStop, RiskProfile, RiskViolationLog
from .serializers import RiskProfileSerializer, EmergencyStopSerializer

logger = logging.getLogger("trademind.risk.views")


class RiskProfileView(APIView):
    """GET /api/v1/risk/profile/  |  PATCH /api/v1/risk/profile/"""
    permission_classes = [IsAuthenticated]

    def _get_profile(self, user):
        return (
            RiskProfile.objects.filter(user=user, is_active=True, is_default=True).first()
            or RiskProfile.objects.filter(user=user, is_active=True).first()
        )

    def get(self, request: Request):
        profile = self._get_profile(request.user)
        if not profile:
            return error_response("RESOURCE_NOT_FOUND", "No risk profile configured.", status_code=404)
        return success_response(data=RiskProfileSerializer(profile).data)

    def patch(self, request: Request):
        profile = self._get_profile(request.user)
        if not profile:
            return error_response("RESOURCE_NOT_FOUND", "No risk profile configured.", status_code=404)
        serializer = RiskProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid risk profile data.",
                                   details=serializer.errors)
        serializer.save()
        return success_response(data=serializer.data, message="Risk profile updated.")


class RiskExposureView(APIView):
    """GET /api/v1/risk/exposure/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from apps.orders.models import Position
        from apps.portfolio.models import Portfolio

        positions = Position.objects.filter(
            user=request.user, status="OPEN", is_paper_trade=False
        ).select_related("trading_pair")

        total_exposure  = sum(
            float(p.quantity) * float(p.current_price) for p in positions
        )
        portfolio_value = 0.0
        portfolios = Portfolio.objects.filter(user=request.user)
        for p in portfolios:
            portfolio_value += float(p.total_balance)

        exposure_pct = (total_exposure / portfolio_value * 100) if portfolio_value > 0 else 0.0

        return success_response(data={
            "open_positions":   positions.count(),
            "total_exposure_usdt": round(total_exposure, 2),
            "portfolio_value_usdt": round(portfolio_value, 2),
            "exposure_pct":     round(exposure_pct, 2),
            "positions":        [
                {
                    "symbol":         p.trading_pair.symbol,
                    "side":           p.side,
                    "quantity":       str(p.quantity),
                    "entry_price":    str(p.entry_price),
                    "current_price":  str(p.current_price),
                    "unrealized_pnl": str(p.unrealized_pnl),
                }
                for p in positions
            ],
        })


class RiskLimitsView(APIView):
    """GET /api/v1/risk/limits/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from django.utils import timezone
        profile = (
            RiskProfile.objects.filter(user=request.user, is_active=True, is_default=True).first()
        )
        if not profile:
            return error_response("RESOURCE_NOT_FOUND", "No risk profile found.", status_code=404)

        today = timezone.now().date()
        daily = DailyLossTracker.objects.filter(user=request.user, date=today).first()

        return success_response(data={
            "limits": {
                "max_risk_per_trade_pct":    str(profile.max_risk_per_trade_pct),
                "max_daily_loss_pct":        str(profile.max_daily_loss_pct),
                "max_weekly_loss_pct":       str(profile.max_weekly_loss_pct),
                "max_open_positions":        profile.max_open_positions,
                "max_portfolio_exposure_pct": str(profile.max_portfolio_exposure_pct),
                "max_drawdown_pct":          str(profile.max_drawdown_pct),
            },
            "current_usage": {
                "daily_realized_loss":   str(daily.realized_loss) if daily else "0",
                "daily_limit_reached":   daily.is_limit_reached if daily else False,
                "trades_today":          daily.trades_count if daily else 0,
            },
        })


class EmergencyStopView(APIView):
    """POST /api/v1/risk/emergency-stop/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        reason = request.data.get("reason", "User triggered emergency stop.")
        if EmergencyStop.objects.filter(user=request.user, is_active=True).exists():
            return error_response("ALREADY_STOPPED", "Emergency stop is already active.")

        EmergencyStop.objects.create(
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            triggered_by="USER",
            reason=reason,
        )
        logger.warning("EMERGENCY STOP triggered by user %s: %s", request.user.id, reason)
        return success_response(message="Emergency stop activated. All automated trading halted.")


class RiskResumeView(APIView):
    """POST /api/v1/risk/resume/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        stop = EmergencyStop.objects.filter(user=request.user, is_active=True).first()
        if not stop:
            return error_response("NOT_STOPPED", "No active emergency stop found.")
        stop.resume()
        logger.info("Emergency stop resumed by user %s", request.user.id)
        return success_response(message="Emergency stop lifted. Trading can resume.")
