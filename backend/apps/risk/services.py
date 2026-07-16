"""
apps/risk/services.py
---------------------
T10 ✅  Risk Engine — FINAL approval authority before any order reaches the exchange.

Rules checked (in order):
  1. Emergency stop active?
  2. Daily loss limit reached?
  3. Max open positions exceeded?
  4. Max portfolio exposure exceeded?
  5. Max risk per trade exceeded?
  6. Max drawdown exceeded?
  7. Consecutive loss cooldown active?
  8. Risk-reward ratio acceptable?
"""
import logging
from decimal import Decimal

logger = logging.getLogger("trademind.risk.services")


class RiskEngineResult:
    def __init__(self, approved: bool, rule: str = "", message: str = ""):
        self.approved = approved
        self.rule     = rule
        self.message  = message

    def __bool__(self):
        return self.approved


class RiskEngine:
    """
    Stateless risk validation service.
    Call validate_order() before submitting any order to the exchange.
    """

    def validate_order(
        self,
        user,
        exchange_account,
        trading_pair_symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float = 0.0,
        is_paper_trade: bool = False,
    ) -> RiskEngineResult:
        """
        T10 ✅  Run all risk checks. Returns RiskEngineResult.
        If approved=False, the order MUST be rejected — no exceptions.
        """
        from apps.risk.models import (
            RiskProfile, EmergencyStop, DailyLossTracker, DrawdownHistory
        )
        from apps.orders.models import Order, Position
        from apps.portfolio.models import Portfolio

        # ── Rule 1: Emergency Stop ────────────────────────────────────────────
        if EmergencyStop.objects.filter(user=user, is_active=True).exists():
            return self._reject("EMERGENCY_STOP_ACTIVE",
                                "Emergency stop is active. No orders can be placed.")

        # Get active risk profile
        profile = (
            RiskProfile.objects.filter(user=user, is_active=True, is_default=True).first()
            or RiskProfile.objects.filter(user=user, is_active=True).first()
        )
        if not profile:
            return self._reject("NO_RISK_PROFILE",
                                "No active risk profile configured.")

        # Get portfolio for balance checks
        try:
            portfolio = Portfolio.objects.get(exchange_account=exchange_account)
            total_balance = float(portfolio.total_balance)
        except Portfolio.DoesNotExist:
            total_balance = 0.0

        if total_balance <= 0 and not is_paper_trade:
            return self._reject("INSUFFICIENT_BALANCE", "Portfolio balance is zero.")

        # ── Rule 2: Daily Loss Limit ──────────────────────────────────────────
        from django.utils import timezone
        today = timezone.now().date()
        daily = DailyLossTracker.objects.filter(user=user, date=today).first()
        if daily and daily.is_limit_reached:
            return self._reject("DAILY_LOSS_LIMIT",
                                f"Daily loss limit reached ({profile.max_daily_loss_pct}%).")

        if daily and total_balance > 0:
            current_loss_pct = abs(float(daily.realized_loss)) / total_balance * 100
            if current_loss_pct >= float(profile.max_daily_loss_pct):
                daily.is_limit_reached = True
                daily.save(update_fields=["is_limit_reached"])
                return self._reject("DAILY_LOSS_LIMIT",
                                    f"Daily loss limit {profile.max_daily_loss_pct}% reached.")

        # ── Rule 3: Max Open Positions ────────────────────────────────────────
        open_positions = Position.objects.filter(
            user=user, status="OPEN", is_paper_trade=is_paper_trade
        ).count()
        if open_positions >= profile.max_open_positions:
            return self._reject("MAX_POSITIONS_EXCEEDED",
                                f"Max open positions ({profile.max_open_positions}) reached.")

        # ── Rule 4: Portfolio Exposure ────────────────────────────────────────
        if total_balance > 0:
            trade_value     = quantity * entry_price
            exposure_pct    = trade_value / total_balance * 100
            if exposure_pct > float(profile.max_single_position_pct):
                return self._reject("POSITION_TOO_LARGE",
                                    f"Position size ({exposure_pct:.1f}%) exceeds "
                                    f"limit ({profile.max_single_position_pct}%).")

        # ── Rule 5: Risk Per Trade ────────────────────────────────────────────
        if stop_loss_price > 0 and total_balance > 0:
            price_risk  = abs(entry_price - stop_loss_price)
            risk_amount = quantity * price_risk
            risk_pct    = risk_amount / total_balance * 100
            if risk_pct > float(profile.max_risk_per_trade_pct):
                return self._reject("RISK_PER_TRADE_EXCEEDED",
                                    f"Trade risk ({risk_pct:.2f}%) exceeds limit "
                                    f"({profile.max_risk_per_trade_pct}%).")

        # ── Rule 6: Max Drawdown ──────────────────────────────────────────────
        latest_dd = DrawdownHistory.objects.filter(user=user).order_by("-recorded_at").first()
        if latest_dd and float(latest_dd.drawdown_pct) >= float(profile.max_drawdown_pct):
            return self._reject("MAX_DRAWDOWN_EXCEEDED",
                                f"Portfolio drawdown ({latest_dd.drawdown_pct}%) "
                                f"exceeded limit ({profile.max_drawdown_pct}%).")

        # ── Rule 7: Consecutive Loss Cooldown ─────────────────────────────────
        # Count consecutive losses from recent closed positions
        recent_positions = list(
            Position.objects.filter(user=user, status="CLOSED", is_paper_trade=is_paper_trade)
            .order_by("-closed_at")[:profile.max_consecutive_losses + 1]
            .values_list("realized_pnl", "closed_at")
        )
        consecutive_losses = 0
        for pnl, closed_at in recent_positions:
            if float(pnl) < 0:
                consecutive_losses += 1
            else:
                break

        if consecutive_losses >= profile.max_consecutive_losses:
            last_loss_time = recent_positions[0][1] if recent_positions else None
            if last_loss_time:
                cooldown_secs = profile.consecutive_loss_cooldown_mins * 60
                elapsed = (timezone.now() - last_loss_time).total_seconds()
                if elapsed < cooldown_secs:
                    remaining = int((cooldown_secs - elapsed) / 60)
                    return self._reject("CONSECUTIVE_LOSS_COOLDOWN",
                                        f"Consecutive losses cooldown active. "
                                        f"Wait {remaining} more minutes.")

        # ── Rule 8: Risk-Reward Ratio ─────────────────────────────────────────
        if risk_reward_ratio > 0 and risk_reward_ratio < 1.0:
            return self._reject("POOR_RISK_REWARD",
                                f"Risk-reward ratio ({risk_reward_ratio:.2f}) is below minimum (1.0).")

        # ── All checks passed ─────────────────────────────────────────────────
        logger.info(
            "Risk approved: user=%s symbol=%s side=%s qty=%s",
            user.id, trading_pair_symbol, side, quantity,
        )
        return RiskEngineResult(approved=True, rule="", message="All risk checks passed.")

    @staticmethod
    def _reject(rule: str, message: str) -> RiskEngineResult:
        logger.warning("Risk REJECTED — rule=%s: %s", rule, message)
        return RiskEngineResult(approved=False, rule=rule, message=message)
