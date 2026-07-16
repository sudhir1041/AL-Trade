"""
apps/risk/serializers.py
T10 ✅
"""
from rest_framework import serializers
from .models import RiskProfile, EmergencyStop, DailyLossTracker


class RiskProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RiskProfile
        fields = [
            "id", "name", "profile_type",
            "max_risk_per_trade_pct", "max_daily_loss_pct",
            "max_weekly_loss_pct",   "max_monthly_loss_pct",
            "max_open_positions",    "max_portfolio_exposure_pct",
            "max_single_position_pct", "max_drawdown_pct",
            "max_consecutive_losses", "consecutive_loss_cooldown_mins",
            "trailing_stop_enabled", "break_even_enabled",
            "partial_profit_enabled", "partial_profit_pct",
            "is_active", "is_default",
        ]
        read_only_fields = ["id"]


class EmergencyStopSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmergencyStop
        fields = ["id", "triggered_by", "reason", "triggered_at", "resumed_at", "is_active"]
        read_only_fields = fields
