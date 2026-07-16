"""
apps/billing/models.py
----------------------
Billing, subscriptions, plans, invoices, and usage tracking.
"""

import uuid

from django.db import models
from django.utils import timezone

from core.models import TenantBaseModel


class PlanTier(models.TextChoices):
    FREE         = "FREE",         "Free"
    STARTER      = "STARTER",      "Starter"
    PROFESSIONAL = "PROFESSIONAL", "Professional"
    ENTERPRISE   = "ENTERPRISE",   "Enterprise"


class SubscriptionStatus(models.TextChoices):
    ACTIVE    = "ACTIVE",    "Active"
    TRIALING  = "TRIALING",  "Trial"
    PAST_DUE  = "PAST_DUE",  "Past Due"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED   = "EXPIRED",   "Expired"


class InvoiceStatus(models.TextChoices):
    DRAFT   = "DRAFT",   "Draft"
    OPEN    = "OPEN",    "Open"
    PAID    = "PAID",    "Paid"
    VOID    = "VOID",    "Void"
    UNCOLLECTIBLE = "UNCOLLECTIBLE", "Uncollectible"


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

class Plan(models.Model):
    """Platform-level subscription plan definition."""

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier            = models.CharField(max_length=20, choices=PlanTier.choices, unique=True)
    name            = models.CharField(max_length=100)
    description     = models.TextField(blank=True)
    price_monthly   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly  = models.CharField(max_length=100, blank=True)

    # Feature limits
    max_exchanges       = models.PositiveSmallIntegerField(default=1)
    max_strategies      = models.PositiveSmallIntegerField(default=1)
    max_open_positions  = models.PositiveSmallIntegerField(default=5)
    max_users           = models.PositiveSmallIntegerField(default=1,
                                                            help_text="For Enterprise team accounts.")
    ai_scoring_enabled  = models.BooleanField(default=False)
    live_trading_enabled = models.BooleanField(default=False)
    white_label_enabled  = models.BooleanField(default=False)
    api_access_enabled   = models.BooleanField(default=False)
    backtesting_enabled  = models.BooleanField(default=True)
    paper_trading_enabled = models.BooleanField(default=True)
    features            = models.JSONField(default=list,
                                            help_text="List of feature keys included in this plan.")

    is_active   = models.BooleanField(default=True)
    sort_order  = models.PositiveSmallIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Plan"
        verbose_name_plural = "Plans"
        ordering            = ["sort_order"]

    def __str__(self) -> str:
        return f"{self.name} (${self.price_monthly}/mo)"


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

class Subscription(TenantBaseModel):
    """A user's current subscription to a plan."""

    user              = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                                           related_name="subscriptions")
    plan              = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status            = models.CharField(max_length=20, choices=SubscriptionStatus.choices,
                                          default=SubscriptionStatus.TRIALING, db_index=True)
    stripe_subscription_id  = models.CharField(max_length=100, blank=True, unique=True, null=True)
    stripe_customer_id      = models.CharField(max_length=100, blank=True)
    current_period_start    = models.DateTimeField(null=True, blank=True)
    current_period_end      = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end    = models.BooleanField(default=False)
    cancelled_at            = models.DateTimeField(null=True, blank=True)
    trial_end               = models.DateTimeField(null=True, blank=True)
    is_yearly               = models.BooleanField(default=False)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Subscription"
        verbose_name_plural = "Subscriptions"
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self) -> str:
        return f"Subscription({self.user_id}, {self.plan.tier}, {self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

    @property
    def is_expired(self) -> bool:
        if self.current_period_end:
            return timezone.now() > self.current_period_end
        return False


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

class Invoice(TenantBaseModel):
    """Billing invoice."""

    user          = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="invoices")
    subscription  = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True,
                                       related_name="invoices")
    stripe_invoice_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    amount_due    = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency      = models.CharField(max_length=10, default="USD")
    status        = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.OPEN)
    invoice_pdf   = models.URLField(blank=True)
    period_start  = models.DateTimeField(null=True, blank=True)
    period_end    = models.DateTimeField(null=True, blank=True)
    paid_at       = models.DateTimeField(null=True, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Invoice"
        verbose_name_plural = "Invoices"
        ordering            = ["-created_at"]

    def __str__(self) -> str:
        return f"Invoice({self.user_id}, ${self.amount_due}, {self.status})"


# ---------------------------------------------------------------------------
# Coupon
# ---------------------------------------------------------------------------

class Coupon(models.Model):
    """Promotional discount codes."""

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code            = models.CharField(max_length=50, unique=True)
    discount_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                           help_text="Percentage discount (0–100).")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text="Fixed amount discount in USD.")
    max_uses        = models.PositiveIntegerField(null=True, blank=True)
    times_used      = models.PositiveIntegerField(default=0)
    valid_from      = models.DateTimeField(default=timezone.now)
    valid_until     = models.DateTimeField(null=True, blank=True)
    applicable_plans = models.JSONField(default=list, help_text="Plan tiers this coupon applies to.")
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self) -> str:
        return f"Coupon({self.code}, {self.discount_pct}% off)"

    @property
    def is_valid(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True
