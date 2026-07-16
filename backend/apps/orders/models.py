"""
apps/orders/models.py
---------------------
Order Management Engine models.

All orders MUST pass through the Risk Engine before reaching the Exchange Service.
Idempotency keys prevent duplicate submissions during retries.
"""

import uuid

from django.db import models
from django.utils import timezone

from core.models import TenantBaseModel


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class OrderSide(models.TextChoices):
    BUY  = "BUY",  "Buy"
    SELL = "SELL", "Sell"


class OrderType(models.TextChoices):
    MARKET       = "MARKET",       "Market"
    LIMIT        = "LIMIT",        "Limit"
    STOP         = "STOP",         "Stop"
    STOP_LIMIT   = "STOP_LIMIT",   "Stop Limit"
    OCO          = "OCO",          "OCO"
    TRAILING_STOP = "TRAILING_STOP", "Trailing Stop"


class OrderStatus(models.TextChoices):
    CREATED          = "CREATED",          "Created"
    SUBMITTED        = "SUBMITTED",        "Submitted to Exchange"
    ACCEPTED         = "ACCEPTED",         "Accepted by Exchange"
    FILLED           = "FILLED",           "Filled"
    PARTIALLY_FILLED = "PARTIALLY_FILLED", "Partially Filled"
    CANCELLED        = "CANCELLED",        "Cancelled"
    REJECTED         = "REJECTED",         "Rejected"
    EXPIRED          = "EXPIRED",          "Expired"


class PositionSide(models.TextChoices):
    LONG  = "LONG",  "Long"
    SHORT = "SHORT", "Short"


class PositionStatus(models.TextChoices):
    OPEN              = "OPEN",              "Open"
    CLOSED            = "CLOSED",            "Closed"
    PARTIALLY_CLOSED  = "PARTIALLY_CLOSED",  "Partially Closed"


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class Order(TenantBaseModel):
    """
    Represents a single trade order in its complete lifecycle.

    All orders are created by the Strategy Engine after passing Risk Engine
    validation. The Exchange Service handles actual submission.
    """

    user             = models.ForeignKey("accounts.User",    on_delete=models.CASCADE, related_name="orders")
    exchange_account = models.ForeignKey("exchanges.ExchangeAccount", on_delete=models.CASCADE, related_name="orders")
    trading_pair     = models.ForeignKey("market.TradingPair", on_delete=models.CASCADE, related_name="orders")
    strategy         = models.ForeignKey("strategies.Strategy", on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="orders")

    # ── Idempotency ─────────────────────────────────────────────────────────
    idempotency_key  = models.CharField(max_length=128, unique=True, db_index=True,
                                         help_text="Prevents duplicate order submission during retries.")
    client_order_id  = models.CharField(max_length=128, blank=True,
                                         help_text="Our generated ID sent to the exchange.")
    exchange_order_id = models.CharField(max_length=256, blank=True, db_index=True,
                                          help_text="Order ID returned by the exchange.")

    # ── Order parameters ────────────────────────────────────────────────────
    side             = models.CharField(max_length=10, choices=OrderSide.choices)
    order_type       = models.CharField(max_length=20, choices=OrderType.choices)
    status           = models.CharField(max_length=20, choices=OrderStatus.choices,
                                         default=OrderStatus.CREATED, db_index=True)

    quantity          = models.DecimalField(max_digits=20, decimal_places=8)
    price             = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True,
                                             help_text="Null for market orders.")
    stop_price        = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    trailing_delta    = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                             help_text="Trailing stop delta as %.")

    # ── Fill information ─────────────────────────────────────────────────────
    filled_quantity   = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    average_fill_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    commission        = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    commission_asset  = models.CharField(max_length=20, blank=True)

    # ── Risk parameters ──────────────────────────────────────────────────────
    stop_loss_price   = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    risk_reward_ratio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    risk_amount_usdt  = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # ── Flags ────────────────────────────────────────────────────────────────
    is_paper_trade   = models.BooleanField(default=False, db_index=True)
    is_backtest      = models.BooleanField(default=False)
    is_manual        = models.BooleanField(default=False, help_text="True if placed manually by user, not by automation.")

    # ── AI context ───────────────────────────────────────────────────────────
    ai_confidence    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_reasoning     = models.TextField(blank=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    submitted_at     = models.DateTimeField(null=True, blank=True)
    filled_at        = models.DateTimeField(null=True, blank=True)
    error_message    = models.TextField(blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["exchange_account", "status"]),
            models.Index(fields=["trading_pair", "-created_at"]),
            models.Index(fields=["exchange_order_id"]),
            models.Index(fields=["idempotency_key"]),
            models.Index(fields=["is_paper_trade", "status"]),
        ]

    def __str__(self) -> str:
        return f"Order({self.side} {self.quantity} {self.trading_pair}, {self.status})"

    @property
    def is_open(self) -> bool:
        return self.status in (OrderStatus.SUBMITTED, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED)

    @property
    def is_complete(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED)

    @property
    def remaining_quantity(self):
        return self.quantity - self.filled_quantity


# ---------------------------------------------------------------------------
# Order Event
# ---------------------------------------------------------------------------

class OrderEvent(models.Model):
    """
    Immutable log of every status transition for an order.
    Used for audit trail, debugging, and customer support.
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order         = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    event_type    = models.CharField(max_length=50, db_index=True)
    old_status    = models.CharField(max_length=20, choices=OrderStatus.choices, blank=True)
    new_status    = models.CharField(max_length=20, choices=OrderStatus.choices, blank=True)
    exchange_data = models.JSONField(default=dict, help_text="Raw exchange response for this event.")
    message       = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Order Event"
        verbose_name_plural = "Order Events"
        ordering            = ["created_at"]
        indexes = [
            models.Index(fields=["order", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"OrderEvent({self.event_type}: {self.old_status} → {self.new_status})"


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------

class Position(TenantBaseModel):
    """
    Represents an open or closed trading position.
    Created when a BUY order fills (LONG) or a SELL order fills (SHORT).
    """

    user             = models.ForeignKey("accounts.User",    on_delete=models.CASCADE, related_name="positions")
    exchange_account = models.ForeignKey("exchanges.ExchangeAccount", on_delete=models.CASCADE, related_name="positions")
    trading_pair     = models.ForeignKey("market.TradingPair", on_delete=models.CASCADE, related_name="positions")
    strategy         = models.ForeignKey("strategies.Strategy", on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="positions")
    entry_order      = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name="opened_position")

    # ── Position basics ──────────────────────────────────────────────────────
    side              = models.CharField(max_length=10, choices=PositionSide.choices)
    status            = models.CharField(max_length=20, choices=PositionStatus.choices,
                                          default=PositionStatus.OPEN, db_index=True)

    # ── Prices ───────────────────────────────────────────────────────────────
    entry_price        = models.DecimalField(max_digits=20, decimal_places=8)
    current_price      = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    quantity           = models.DecimalField(max_digits=20, decimal_places=8)
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=8)

    # ── PnL ─────────────────────────────────────────────────────────────────
    unrealized_pnl    = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    realized_pnl      = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    commission_paid   = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # ── Leverage (futures) ───────────────────────────────────────────────────
    leverage          = models.PositiveSmallIntegerField(default=1)
    margin            = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    liquidation_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # ── Risk management ──────────────────────────────────────────────────────
    stop_loss_price       = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_price     = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    trailing_stop_pct     = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    trailing_stop_price   = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    break_even_triggered  = models.BooleanField(default=False)
    partial_close_done    = models.BooleanField(default=False)

    # ── Flags ────────────────────────────────────────────────────────────────
    is_paper_trade  = models.BooleanField(default=False, db_index=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    opened_at  = models.DateTimeField(default=timezone.now)
    closed_at  = models.DateTimeField(null=True, blank=True)

    # ── AI context ───────────────────────────────────────────────────────────
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Position"
        verbose_name_plural = "Positions"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["exchange_account", "status"]),
            models.Index(fields=["trading_pair", "status"]),
            models.Index(fields=["is_paper_trade", "status"]),
        ]

    def __str__(self) -> str:
        return f"Position({self.side} {self.quantity} {self.trading_pair}, {self.status})"

    @property
    def pnl_pct(self) -> float:
        """Return unrealised PnL as a percentage of entry value."""
        entry_value = float(self.entry_price) * float(self.quantity)
        if entry_value == 0:
            return 0.0
        return (float(self.unrealized_pnl) / entry_value) * 100
