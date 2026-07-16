"""
apps/orders/serializers.py
T11 ✅
"""
from rest_framework import serializers
from .models import Order, OrderEvent, Position


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Order
        fields = [
            "exchange_account", "trading_pair", "strategy",
            "side", "order_type", "quantity", "price",
            "stop_price", "stop_loss_price", "take_profit_price",
            "idempotency_key", "is_paper_trade", "is_manual",
        ]

    def validate(self, data):
        if data["order_type"] == "LIMIT" and not data.get("price"):
            raise serializers.ValidationError({"price": "Price is required for LIMIT orders."})
        if data["order_type"] in ("STOP", "STOP_LIMIT") and not data.get("stop_price"):
            raise serializers.ValidationError({"stop_price": "stop_price is required for STOP orders."})
        return data


class OrderSerializer(serializers.ModelSerializer):
    symbol           = serializers.CharField(source="trading_pair.symbol", read_only=True)
    exchange_name    = serializers.CharField(source="exchange_account.exchange.name", read_only=True)
    strategy_name    = serializers.CharField(source="strategy.name", read_only=True)
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            "id", "symbol", "exchange_name", "strategy_name",
            "side", "order_type", "status",
            "quantity", "price", "stop_price",
            "filled_quantity", "remaining_quantity",
            "average_fill_price", "commission", "commission_asset",
            "stop_loss_price", "take_profit_price", "risk_reward_ratio",
            "is_paper_trade", "is_manual", "ai_confidence",
            "idempotency_key", "client_order_id", "exchange_order_id",
            "submitted_at", "filled_at", "created_at", "error_message",
        ]
        read_only_fields = fields

    def get_remaining_quantity(self, obj):
        return str(obj.remaining_quantity)


class OrderEventSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderEvent
        fields = ["id", "event_type", "old_status", "new_status", "message", "created_at"]


class PositionSerializer(serializers.ModelSerializer):
    symbol        = serializers.CharField(source="trading_pair.symbol", read_only=True)
    exchange_name = serializers.CharField(source="exchange_account.exchange.name", read_only=True)
    pnl_pct       = serializers.SerializerMethodField()

    class Meta:
        model  = Position
        fields = [
            "id", "symbol", "exchange_name", "side", "status",
            "entry_price", "current_price", "quantity", "remaining_quantity",
            "unrealized_pnl", "realized_pnl", "pnl_pct",
            "leverage", "liquidation_price",
            "stop_loss_price", "take_profit_price",
            "trailing_stop_pct", "break_even_triggered",
            "is_paper_trade", "opened_at", "closed_at", "ai_confidence",
        ]

    def get_pnl_pct(self, obj):
        return round(obj.pnl_pct, 4)
