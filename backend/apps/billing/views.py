"""
apps/billing/views.py
T19 ✅  Billing & subscription endpoints.

GET  /billing/plans/              – list available plans
GET  /billing/subscription/       – current subscription
POST /billing/subscription/       – create / upgrade
POST /billing/subscription/cancel/– cancel at period end
GET  /billing/invoices/           – invoice history
POST /billing/coupons/validate/   – validate a coupon code
"""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import error_response, success_response, created_response
from .models import Plan, Subscription, Invoice, Coupon, SubscriptionStatus
from .serializers import (
    PlanSerializer, SubscriptionSerializer,
    InvoiceSerializer, CouponValidateSerializer,
)

logger = logging.getLogger("trademind.billing.views")


class PlanListView(APIView):
    """GET /api/v1/billing/plans/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        plans = Plan.objects.filter(is_active=True).order_by("sort_order")
        return success_response(data=PlanSerializer(plans, many=True).data)


class SubscriptionView(APIView):
    """GET /api/v1/billing/subscription/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        sub = (
            Subscription.objects.filter(user=request.user)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )
        if not sub:
            # Auto-create free plan subscription
            free_plan = Plan.objects.filter(tier="FREE").first()
            if free_plan:
                sub = Subscription.objects.create(
                    user=request.user,
                    tenant_id=request.user.tenant_id or request.user.id,
                    plan=free_plan,
                    status=SubscriptionStatus.ACTIVE,
                )
            else:
                return error_response("NO_PLAN", "No subscription found.", status_code=404)

        return success_response(data=SubscriptionSerializer(sub).data)

    def post(self, request: Request):
        """Create or upgrade subscription."""
        plan_id  = request.data.get("plan_id")
        is_yearly = request.data.get("is_yearly", False)

        try:
            plan = Plan.objects.get(pk=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Plan not found.", status_code=404)

        # Cancel existing active subscription
        Subscription.objects.filter(
            user=request.user,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
        ).update(status=SubscriptionStatus.CANCELLED)

        # Create new subscription
        sub = Subscription.objects.create(
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            is_yearly=is_yearly,
        )

        # TODO: integrate Stripe checkout session here
        logger.info("Subscription created: user=%s plan=%s", request.user.id, plan.tier)
        return created_response(
            data=SubscriptionSerializer(sub).data,
            message=f"Subscribed to {plan.name}.",
        )


class SubscriptionCancelView(APIView):
    """POST /api/v1/billing/subscription/cancel/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        sub = Subscription.objects.filter(
            user=request.user,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
        ).first()
        if not sub:
            return error_response("NO_ACTIVE_SUBSCRIPTION", "No active subscription to cancel.")

        sub.cancel_at_period_end = True
        sub.save(update_fields=["cancel_at_period_end"])
        # TODO: call stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
        return success_response(
            message="Subscription will cancel at the end of the current billing period."
        )


class InvoiceListView(APIView):
    """GET /api/v1/billing/invoices/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        invoices = Invoice.objects.filter(user=request.user).order_by("-created_at")[:24]
        return success_response(data=InvoiceSerializer(invoices, many=True).data)


class CouponValidateView(APIView):
    """POST /api/v1/billing/coupons/validate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = CouponValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid request.", details=serializer.errors)

        code = serializer.validated_data["code"].upper()
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return error_response("INVALID_COUPON", "Coupon code not found.")

        if not coupon.is_valid:
            return error_response("COUPON_EXPIRED", "This coupon is no longer valid.")

        return success_response(data={
            "code":            coupon.code,
            "discount_pct":    str(coupon.discount_pct),
            "discount_amount": str(coupon.discount_amount),
            "applicable_plans": coupon.applicable_plans,
        }, message="Coupon is valid.")
