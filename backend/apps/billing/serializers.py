"""
apps/billing/serializers.py
T19 ✅
"""
from rest_framework import serializers
from .models import Plan, Subscription, Invoice, Coupon


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Plan
        fields = [
            "id", "tier", "name", "description",
            "price_monthly", "price_yearly",
            "max_exchanges", "max_strategies", "max_open_positions",
            "max_users", "ai_scoring_enabled", "live_trading_enabled",
            "white_label_enabled", "api_access_enabled",
            "backtesting_enabled", "paper_trading_enabled",
            "features", "is_active", "sort_order",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name",  read_only=True)
    plan_tier = serializers.CharField(source="plan.tier",  read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model  = Subscription
        fields = [
            "id", "plan", "plan_name", "plan_tier",
            "status", "is_active", "is_yearly",
            "current_period_start", "current_period_end",
            "cancel_at_period_end", "trial_end",
        ]

    def get_is_active(self, obj):
        return obj.is_active


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Invoice
        fields = [
            "id", "amount_due", "amount_paid", "currency",
            "status", "invoice_pdf", "period_start", "period_end",
            "paid_at", "created_at",
        ]


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
