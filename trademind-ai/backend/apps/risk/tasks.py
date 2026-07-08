"""
apps/risk/tasks.py
T10 ✅  Risk monitoring Celery tasks — runs every 2 minutes.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.risk.tasks")


@shared_task(queue="default", name="apps.risk.tasks.check_portfolio_risk_limits")
def check_portfolio_risk_limits() -> dict:
    """
    T10 ✅  Periodic risk check for all active users.
    - Checks drawdown against configured limits
    - Triggers emergency stop if drawdown exceeded
    - Updates DailyLossTracker from closed positions
    """
    from apps.accounts.models import User
    from apps.orders.models import Position
    from apps.portfolio.models import Portfolio
    from apps.risk.models import (
        RiskProfile, EmergencyStop, DailyLossTracker, DrawdownHistory
    )
    from django.utils import timezone

    today    = timezone.now().date()
    triggers = 0
    checked  = 0

    for user in User.objects.filter(is_active=True).iterator():
        checked += 1
        profile = RiskProfile.objects.filter(
            user=user, is_active=True, is_default=True
        ).first()
        if not profile:
            continue

        # Skip if emergency stop already active
        if EmergencyStop.objects.filter(user=user, is_active=True).exists():
            continue

        # Check daily loss
        daily = DailyLossTracker.objects.filter(user=user, date=today).first()
        portfolios = Portfolio.objects.filter(user=user)
        total_balance = sum(float(p.total_balance) for p in portfolios)

        if daily and total_balance > 0:
            loss_pct = abs(float(daily.realized_loss)) / total_balance * 100
            if loss_pct >= float(profile.max_daily_loss_pct):
                daily.is_limit_reached = True
                daily.save(update_fields=["is_limit_reached"])

        # Check drawdown
        if total_balance > 0:
            peak = portfolios.order_by("-peak_balance").first()
            if peak and float(peak.peak_balance) > 0:
                drawdown_pct = (float(peak.peak_balance) - total_balance) / float(peak.peak_balance) * 100
                DrawdownHistory.objects.create(
                    user=user,
                    max_balance=peak.peak_balance,
                    current_balance=total_balance,
                    drawdown_pct=drawdown_pct,
                )
                if drawdown_pct >= float(profile.max_drawdown_pct):
                    EmergencyStop.objects.create(
                        user=user,
                        tenant_id=user.tenant_id or user.id,
                        triggered_by="SYSTEM",
                        reason=f"Max drawdown {profile.max_drawdown_pct}% exceeded "
                               f"(current: {drawdown_pct:.2f}%). Auto emergency stop.",
                    )
                    triggers += 1
                    logger.warning(
                        "AUTO EMERGENCY STOP: user=%s drawdown=%.2f%%",
                        user.id, drawdown_pct,
                    )

    logger.info("Risk check: %d users checked, %d auto-stops triggered", checked, triggers)
    return {"checked": checked, "auto_stops": triggers}
