"""
apps/strategies/serializers.py
T9 ✅
"""
from rest_framework import serializers
from .models import Strategy, UserStrategy, StrategyPerformance, BacktestJob


class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Strategy
        fields = [
            "id", "name", "slug", "strategy_type", "description",
            "suitable_regimes", "unsuitable_regimes",
            "min_timeframe", "max_timeframe",
            "default_params", "config_schema",
            "is_active", "requires_premium", "sort_order",
        ]


class UserStrategySerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source="strategy.name", read_only=True)
    strategy_type = serializers.CharField(source="strategy.strategy_type", read_only=True)

    class Meta:
        model  = UserStrategy
        fields = [
            "id", "strategy", "strategy_name", "strategy_type",
            "name", "parameters", "timeframes", "trading_pairs",
            "exchanges", "automation_level", "min_confidence_score",
            "max_trades_per_day", "trading_sessions",
            "risk_profile", "is_active", "is_paper_mode",
        ]


class StrategyPerformanceSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source="user_strategy.name", read_only=True)

    class Meta:
        model  = StrategyPerformance
        fields = [
            "strategy_name", "total_trades", "winning_trades", "losing_trades",
            "win_rate_pct", "avg_win_usdt", "avg_loss_usdt", "profit_factor",
            "total_pnl_usdt", "net_pnl_usdt",
            "sharpe_ratio", "sortino_ratio", "max_drawdown_pct",
            "avg_holding_hours", "first_trade_at", "last_trade_at",
        ]


class BacktestJobSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source="strategy.name", read_only=True)
    symbol        = serializers.CharField(source="trading_pair.symbol", read_only=True)

    class Meta:
        model  = BacktestJob
        fields = [
            "id", "strategy_name", "symbol", "timeframe",
            "start_date", "end_date", "initial_balance",
            "parameters", "status", "results",
            "started_at", "completed_at", "error_message",
        ]
        read_only_fields = ["id", "status", "results", "started_at", "completed_at", "error_message"]
