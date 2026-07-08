"""
apps/risk/models.py
-------------------
Risk Management Engine models.

The Risk Engine is the FINAL authority before any order reaches the exchange.
Every order must be validated against the user's active RiskProfile.
"""

import uuid

from django.db import models
from django.utils import timezone

from core.models import TenantBaseModel


class RiskProfileType(models.TextChoices):
    CONSERVATIVE = "CONSERVATIVE", "Conservative"
    MODERATE     = "MODERATE",     "Moderate"
    AGGRESSIVE   = "AGGRESSIVE",   "Aggressive"
    CUSTOM       = "CUSTOM",       "Custom"


class EmergencyStopTrigger(models.TextChoices):
    USER   = "USER",   "User Triggered"
    SYSTEM = "SYSTEM", "System Triggered"


# ---------------------------------------------------------------------------
# Risk Profile
# ---------------------------------------------------------------------------

class RiskProfile(TenantBaseModel):
    """
    Defines all risk parameters for a user's trading activity.
    One user can have multiple profiles, but only one can be active at a time.
    """

    user         = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="risk_profiles",
    )
    name         = models.CharField(max_length=100, verbose_name="Profile Name")
    profile_type = models.CharField(max_length=20, choices=RiskProfileType.choices,
                                    default=RiskProfileType.MODERATE)

    # ── Per-trade limits ────────────────────────────────────────────────────
    max_risk_per_trade_pct  = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="Maximum % of portfolio balance to risk on a single trade.",
    )

    # ── Loss limits ─────────────────────────────────────────────────────────
    max_daily_loss_pct      = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    max_weekly_loss_pct     = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    max_monthly_loss_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)

    # ── Exposure limits ─────────────────────────────────────────────────────
    max_open_positions       = models.PositiveIntegerField(default=5)
    max_portfolio_exposure_pct = models.DecimalField(max_digits=5, decimal_places=2, default=50.0,
                                                      help_text="Max % of portfolio in open positions.")
    max_single_position_pct  = models.DecimalField(max_digits=5, decimal_places=2, default=20.0,
                                                    help_text="Max % of portfolio in a single position.")

    # ── Drawdown ─────────────────────────────────────────────────────────────
    max_drawdown_pct        = models.DecimalField(max_digits=5, decimal_places=2, default=15.0,
                                                   help_text="Auto-pause trading if drawdown exceeds this %.")

    # ── Consecutive loss protection ──────────────────────────────────────────
    max_consecutive_losses         = models.PositiveIntegerField(default=3)
    consecutive_loss_cooldown_mins = models.PositiveIntegerField(default=60,
                                                                  help_text="Pause trading for this many minutes after hitting max consecutive losses.")

    # ── Position management ──────────────────────────────────────────────────
    trailing_stop_enabled   = models.BooleanField(default=True)
    break_even_enabled      = models.BooleanField(default=True)
    partial_profit_enabled  = models.BooleanField(default=True)
    partial_profit_pct      = models.DecimalField(max_digits=5, decimal_places=2, default=50.0,
                                                   help_text="% of position to close at first take-profit level.")

    # ── Metadata ─────────────────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False,
                                      help_text="Exactly one profile per user should be marked as default.")

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Risk Profile"
        verbose_name_plural = "Risk Profiles"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self) -> str:
        return f"RiskProfile({self.name}, {self.profile_type}, user={self.user_id})"

    def save(self, *args, **kwargs):
        # Ensure only one default per user
        if self.is_default:
            RiskProfile.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Emergency Stop
# ---------------------------------------------------------------------------

class EmergencyStop(TenantBaseModel):
    """
    Records emergency stop events. While is_active=True, NO new orders
    can be placed by the user. Overrides all strategy automation.
    """

    user         = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="emergency_stops",
    )
    triggered_by = models.CharField(max_length=20, choices=EmergencyStopTrigger.choices,
                                    default=EmergencyStopTrigger.USER)
    reason       = models.TextField(help_text="Why was the emergency stop triggered?")
    triggered_at = models.DateTimeField(default=timezone.now)
    resumed_at   = models.DateTimeField(null=True, blank=True)
    is_active    = models.BooleanField(default=True, db_index=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Emergency Stop"
        verbose_name_plural = "Emergency Stops"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "RESOLVED"
        return f"EmergencyStop({status}, user={self.user_id}, trigger={self.triggered_by})"

    def resume(self) -> None:
        """Deactivate the emergency stop and record the resume time."""
        self.is_active = False
        self.resumed_at = timezone.now()
        self.save(update_fields=["is_active", "resumed_at"])


# ---------------------------------------------------------------------------
# Daily Loss Tracker
# ---------------------------------------------------------------------------

class DailyLossTracker(models.Model):
    """
    Tracks realised and unrealised losses per user per calendar day.
    Updated in real-time as trades close and positions move.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="daily_loss_records")
    date            = models.DateField(db_index=True)
    realized_loss   = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    unrealized_loss = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    trades_count    = models.PositiveIntegerField(default=0)
    is_limit_reached = models.BooleanField(default=False, db_index=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Daily Loss Tracker"
        verbose_name_plural = "Daily Loss Trackers"
        unique_together     = [("user", "date")]
        ordering            = ["-date"]

    def __str__(self) -> str:
        return f"DailyLoss(user={self.user_id}, date={self.date}, loss={self.realized_loss})"


# ---------------------------------------------------------------------------
# Drawdown History
# ---------------------------------------------------------------------------

class DrawdownHistory(models.Model):
    """Periodic snapshots of portfolio drawdown for charting and alerts."""

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user             = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="drawdown_history")
    max_balance      = models.DecimalField(max_digits=20, decimal_places=8)
    current_balance  = models.DecimalField(max_digits=20, decimal_places=8)
    drawdown_pct     = models.DecimalField(max_digits=6, decimal_places=2)
    recorded_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Drawdown History"
        verbose_name_plural = "Drawdown History"
        ordering            = ["-recorded_at"]
        indexes = [
            models.Index(fields=["user", "-recorded_at"]),
        ]

    def __str__(self) -> str:
        return f"Drawdown(user={self.user_id}, {self.drawdown_pct}%, at={self.recorded_at:%Y-%m-%d})"


# ---------------------------------------------------------------------------
# Risk Violation Log
# ---------------------------------------------------------------------------

class RiskViolationLog(models.Model):
    """
    Immutable log of every trade rejected by the Risk Engine.
    Used for audit, debugging, and user reporting.
    """

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="risk_violations")
    risk_profile   = models.ForeignKey(RiskProfile, on_delete=models.SET_NULL, null=True)
    rule_name      = models.CharField(max_length=100, db_index=True)
    rule_value     = models.CharField(max_length=100, blank=True, help_text="Configured limit.")
    actual_value   = models.CharField(max_length=100, blank=True, help_text="Actual value that triggered the violation.")
    order_data     = models.JSONField(default=dict, help_text="Snapshot of the rejected order.")
    created_at     = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Risk Violation Log"
        verbose_name_plural = "Risk Violation Logs"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["rule_name", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"RiskViolation(rule={self.rule_name}, user={self.user_id})"
