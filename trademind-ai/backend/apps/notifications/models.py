"""
apps/notifications/models.py
-----------------------------
Notification system models – channels, templates, delivery queue, and logs.
"""

import uuid

from django.db import models

from core.models import TenantBaseModel


class NotificationChannel(models.TextChoices):
    EMAIL    = "EMAIL",    "Email"
    TELEGRAM = "TELEGRAM", "Telegram"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    PUSH     = "PUSH",     "Push Notification"
    DISCORD  = "DISCORD",  "Discord"
    SLACK    = "SLACK",    "Slack"


class NotificationEventType(models.TextChoices):
    TRADE_EXECUTED       = "TRADE_EXECUTED",       "Trade Executed"
    POSITION_CLOSED      = "POSITION_CLOSED",      "Position Closed"
    STOP_LOSS_TRIGGERED  = "STOP_LOSS_TRIGGERED",  "Stop Loss Triggered"
    TAKE_PROFIT_REACHED  = "TAKE_PROFIT_REACHED",  "Take Profit Reached"
    API_FAILURE          = "API_FAILURE",           "API Failure"
    EXCHANGE_OFFLINE     = "EXCHANGE_OFFLINE",      "Exchange Offline"
    DAILY_SUMMARY        = "DAILY_SUMMARY",         "Daily Summary"
    RISK_WARNING         = "RISK_WARNING",          "Risk Warning"
    EMERGENCY_STOP       = "EMERGENCY_STOP",        "Emergency Stop"
    SCANNER_ALERT        = "SCANNER_ALERT",         "Scanner Alert"
    SYSTEM_ALERT         = "SYSTEM_ALERT",          "System Alert"
    BILLING_EVENT        = "BILLING_EVENT",         "Billing Event"


class DeliveryStatus(models.TextChoices):
    PENDING   = "PENDING",   "Pending"
    SENT      = "SENT",      "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    FAILED    = "FAILED",    "Failed"
    SKIPPED   = "SKIPPED",   "Skipped (Channel Disabled)"


# ---------------------------------------------------------------------------
# Notification Template
# ---------------------------------------------------------------------------

class NotificationTemplate(models.Model):
    """Platform-level reusable notification templates per event type and channel."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=NotificationEventType.choices, db_index=True)
    channel    = models.CharField(max_length=20, choices=NotificationChannel.choices)
    subject    = models.CharField(max_length=255, blank=True, help_text="Email subject / Telegram title.")
    body       = models.TextField(help_text="Template body. Use {{variable}} placeholders.")
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Notification Template"
        verbose_name_plural = "Notification Templates"
        unique_together     = [("event_type", "channel")]
        ordering            = ["event_type", "channel"]

    def __str__(self) -> str:
        return f"Template({self.event_type} → {self.channel})"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class Notification(TenantBaseModel):
    """
    A notification instance created when a platform event occurs.
    One Notification → one or more NotificationDelivery records (one per channel).
    """

    user       = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    event_type = models.CharField(max_length=50, choices=NotificationEventType.choices, db_index=True)
    title      = models.CharField(max_length=255)
    message    = models.TextField()
    payload    = models.JSONField(default=dict, help_text="Structured data for rendering (e.g. trade details).")
    is_read    = models.BooleanField(default=False, db_index=True)
    read_at    = models.DateTimeField(null=True, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification({self.event_type}, user={self.user_id}, read={self.is_read})"

    def mark_read(self) -> None:
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])


# ---------------------------------------------------------------------------
# Notification Delivery
# ---------------------------------------------------------------------------

class NotificationDelivery(models.Model):
    """
    Delivery attempt record for a specific channel.
    Supports retry logic with exponential backoff.
    """

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification   = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="deliveries")
    channel        = models.CharField(max_length=20, choices=NotificationChannel.choices, db_index=True)
    status         = models.CharField(max_length=20, choices=DeliveryStatus.choices,
                                       default=DeliveryStatus.PENDING, db_index=True)
    attempts       = models.PositiveSmallIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    delivered_at   = models.DateTimeField(null=True, blank=True)
    error_message  = models.TextField(blank=True)
    external_id    = models.CharField(max_length=256, blank=True, help_text="Message ID from external service.")
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Notification Delivery"
        verbose_name_plural = "Notification Deliveries"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["notification", "channel"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Delivery({self.channel}, {self.status}, attempts={self.attempts})"
