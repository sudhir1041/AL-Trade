"""
apps/exchanges/models.py
------------------------
Exchange connectivity and account management for TradeMind AI.

Models
------
- Exchange           : Supported exchange registry
- ExchangeAccount    : User-owned exchange credentials (TenantBaseModel)
- ExchangeConnection : WebSocket / REST connection lifecycle log
- ExchangeLog        : Per-request audit log for exchange API calls
"""

import uuid

from django.db import models

from apps.accounts.models import User
from core.models import TenantBaseModel

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ConnectionStatus(models.TextChoices):
    CONNECTED = "CONNECTED", "Connected"
    DISCONNECTED = "DISCONNECTED", "Disconnected"
    ERROR = "ERROR", "Error"
    TESTING = "TESTING", "Testing"


# ---------------------------------------------------------------------------
# Exchange
# ---------------------------------------------------------------------------


class Exchange(models.Model):
    """
    Registry of exchanges supported by the platform.
    Not tenant-scoped — shared across all tenants.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Name")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    logo_url = models.URLField(max_length=512, blank=True, verbose_name="Logo URL")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    supports_futures = models.BooleanField(
        default=False, verbose_name="Supports Futures"
    )
    supports_spot = models.BooleanField(default=True, verbose_name="Supports Spot")
    supports_websocket = models.BooleanField(
        default=False, verbose_name="Supports WebSocket"
    )
    sandbox_available = models.BooleanField(
        default=False, verbose_name="Sandbox Available"
    )
    phase = models.IntegerField(
        default=1,
        verbose_name="Integration Phase",
        help_text="1 = Phase 1 (core), 2 = Phase 2 (extended).",
    )
    api_docs_url = models.URLField(
        max_length=512, blank=True, verbose_name="API Docs URL"
    )
    rate_limit_per_minute = models.IntegerField(
        default=60, verbose_name="Rate Limit / Minute"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exchange"
        verbose_name_plural = "Exchanges"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "phase"]),
        ]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# ExchangeAccount
# ---------------------------------------------------------------------------


class ExchangeAccount(TenantBaseModel):
    """
    Stores encrypted API credentials for a user's exchange account.
    Encryption/decryption is handled in the service layer, not here.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exchange_accounts",
        verbose_name="User",
    )
    exchange = models.ForeignKey(
        Exchange,
        on_delete=models.PROTECT,
        related_name="accounts",
        verbose_name="Exchange",
    )
    label = models.CharField(max_length=255, verbose_name="Label")
    # Credentials — stored encrypted; never log or expose these fields
    api_key_encrypted = models.TextField(verbose_name="API Key (encrypted)")
    api_secret_encrypted = models.TextField(verbose_name="API Secret (encrypted)")
    api_passphrase_encrypted = models.TextField(
        blank=True,
        verbose_name="API Passphrase (encrypted)",
        help_text="Required by some exchanges (e.g., KuCoin).",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_testnet = models.BooleanField(default=False, verbose_name="Testnet / Sandbox")
    permissions = models.JSONField(
        default=list,
        verbose_name="Permissions",
        help_text="Exchange-reported permissions for this API key.",
    )
    last_sync_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Last Synced At"
    )
    balance_synced_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Balance Synced At"
    )
    connection_status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.DISCONNECTED,
        verbose_name="Connection Status",
    )

    class Meta(TenantBaseModel.Meta):
        verbose_name = "Exchange Account"
        verbose_name_plural = "Exchange Accounts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "exchange"]),
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["connection_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.label} – {self.exchange} ({self.user_id})"


# ---------------------------------------------------------------------------
# ExchangeConnection
# ---------------------------------------------------------------------------


class ExchangeConnection(models.Model):
    """
    Lifecycle record for each WebSocket / REST session with an exchange.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.CASCADE,
        related_name="connections",
        verbose_name="Exchange Account",
    )
    connected_at = models.DateTimeField(auto_now_add=True, verbose_name="Connected At")
    disconnected_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Disconnected At"
    )
    status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.CONNECTED,
        verbose_name="Status",
    )
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    websocket_session_id = models.CharField(
        max_length=255, blank=True, verbose_name="WebSocket Session ID"
    )

    class Meta:
        verbose_name = "Exchange Connection"
        verbose_name_plural = "Exchange Connections"
        ordering = ["-connected_at"]
        indexes = [
            models.Index(fields=["exchange_account", "status"]),
            models.Index(fields=["connected_at"]),
        ]

    def __str__(self) -> str:
        return f"Connection({self.exchange_account_id}, {self.status})"


# ---------------------------------------------------------------------------
# ExchangeLog
# ---------------------------------------------------------------------------


class ExchangeLog(models.Model):
    """
    Append-only log of every API call made to an exchange.
    Useful for debugging, rate-limit analysis, and compliance auditing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Exchange Account",
    )
    action = models.CharField(max_length=128, verbose_name="Action")
    request_data = models.JSONField(default=dict, verbose_name="Request Data")
    response_data = models.JSONField(default=dict, verbose_name="Response Data")
    status_code = models.IntegerField(verbose_name="HTTP Status Code")
    latency_ms = models.IntegerField(verbose_name="Latency (ms)")
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Exchange Log"
        verbose_name_plural = "Exchange Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["exchange_account", "action"]),
            models.Index(fields=["exchange_account", "created_at"]),
            models.Index(fields=["status_code"]),
        ]

    def __str__(self) -> str:
        return f"ExchangeLog({self.action}, status={self.status_code}, {self.latency_ms}ms)"
