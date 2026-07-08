from rest_framework import serializers
from .models import Portfolio, PortfolioAsset, PnLHistory, PortfolioHistory


class PortfolioAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PortfolioAsset
        fields = ["asset", "quantity", "avg_buy_price", "current_price",
                  "value_usdt", "allocation_pct", "unrealized_pnl", "unrealized_pct"]


class PortfolioSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source="exchange_account.exchange.name", read_only=True)
    return_pct    = serializers.SerializerMethodField()
    assets        = PortfolioAssetSerializer(many=True, read_only=True)

    class Meta:
        model  = Portfolio
        fields = [
            "id", "exchange_name", "total_balance", "available_balance",
            "locked_balance", "unrealized_pnl", "realized_pnl", "total_pnl",
            "initial_balance", "peak_balance", "max_drawdown_pct",
            "return_pct", "assets", "last_synced_at", "is_paper",
        ]

    def get_return_pct(self, obj):
        return round(obj.return_pct, 4)


class PnLHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PnLHistory
        fields = ["date", "daily_pnl", "cumulative_pnl", "portfolio_value",
                  "trade_count", "win_count", "loss_count", "win_rate_pct"]


class PortfolioHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PortfolioHistory
        fields = ["total_balance", "unrealized_pnl", "recorded_at"]
