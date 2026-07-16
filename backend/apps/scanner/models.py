"""
apps/scanner/models.py
----------------------
Market Scanner models – stores scan jobs, results, candidate/rejected coins,
and per-user scanner configuration.
"""

import uuid

from django.db import models

from core.models import TenantBaseModel


class ScannerJobStatus(models.TextChoices):
    PENDING   = "PENDING",   "Pending"
    RUNNING   = "RUNNING",   "Running"
    COMPLETED = "COMPLETED", "Completed"
    FAILED    = "FAILED",    "Failed"


class TrendDirection(models.TextChoices):
    BULLISH  = "BULLISH",  "Bullish"
    BEARISH  = "BEARISH",  "Bearish"
    SIDEWAYS = "SIDEWAYS", "Sideways"
    UNKNOWN  = "UNKNOWN",  "Unknown"


# ---------------------------------------------------------------------------
# Scanner Job
# ---------------------------------------------------------------------------

class ScannerJob(TenantBaseModel):
    """
    Represents a single scanner execution cycle.
    One job is created each time the scanner worker runs.
    """

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scanner_jobs",
        help_text="Null for system-triggered scans.",
    )
    status         = models.CharField(max_length=20, choices=ScannerJobStatus.choices, default=ScannerJobStatus.PENDING)
    started_at     = models.DateTimeField(null=True, blank=True)
    completed_at   = models.DateTimeField(null=True, blank=True)
    pairs_scanned  = models.PositiveIntegerField(default=0)
    candidates_found = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)
    duration_ms    = models.PositiveIntegerField(default=0, help_text="Scan duration in milliseconds.")
    error_message  = models.TextField(blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Scanner Job"
        verbose_name_plural = "Scanner Jobs"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"ScannerJob({self.status}, {self.pairs_scanned} pairs, {self.candidates_found} candidates)"


# ---------------------------------------------------------------------------
# Scanner Result
# ---------------------------------------------------------------------------

class ScannerResult(models.Model):
    """
    Individual coin scoring result within a ScannerJob.
    Stores the AI/rule-based scores and key filter outputs.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scanner_job     = models.ForeignKey(ScannerJob, on_delete=models.CASCADE, related_name="results")
    trading_pair    = models.ForeignKey("market.TradingPair", on_delete=models.CASCADE, related_name="scanner_results")

    # Scores (0–100)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_score       = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Trend & momentum
    trend_direction  = models.CharField(max_length=20, choices=TrendDirection.choices, default=TrendDirection.UNKNOWN)
    rsi_value        = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    macd_signal      = models.CharField(max_length=20, blank=True)   # e.g. "BULLISH_CROSSOVER"

    # Volume & liquidity
    volume_24h_usdt  = models.DecimalField(max_digits=24, decimal_places=2, null=True, blank=True)
    volume_spike     = models.BooleanField(default=False)
    spread_pct       = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # Correlation
    btc_correlation  = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    eth_correlation  = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    # Detailed factor breakdown (JSON for flexibility)
    factors          = models.JSONField(default=dict, help_text="Key indicator values that contributed to the score.")
    is_candidate     = models.BooleanField(default=False, db_index=True)
    rejection_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Scanner Result"
        verbose_name_plural = "Scanner Results"
        ordering            = ["-confidence_score"]
        indexes = [
            models.Index(fields=["scanner_job", "is_candidate"]),
            models.Index(fields=["trading_pair", "-created_at"]),
            models.Index(fields=["scanner_job", "-confidence_score"]),
        ]

    def __str__(self) -> str:
        flag = "✓" if self.is_candidate else "✗"
        return f"[{flag}] {self.trading_pair} — score={self.confidence_score}"


# ---------------------------------------------------------------------------
# Scanner Settings
# ---------------------------------------------------------------------------

class ScannerSettings(TenantBaseModel):
    """
    Per-user scanner configuration.  One row per user.
    Provides sensible defaults that users can override.
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="scanner_settings",
    )

    # Volume & liquidity filters
    min_volume_usdt    = models.DecimalField(max_digits=20, decimal_places=2, default=500000,
                                              help_text="Minimum 24h volume in USDT.")
    min_liquidity_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    max_spread_pct     = models.DecimalField(max_digits=6, decimal_places=4, default=0.5,
                                              help_text="Maximum bid-ask spread as a percentage.")

    # Volatility filters
    volatility_min     = models.DecimalField(max_digits=6, decimal_places=4, default=0.005,
                                              help_text="Minimum ATR/price ratio.")
    volatility_max     = models.DecimalField(max_digits=6, decimal_places=4, default=0.15,
                                              help_text="Maximum ATR/price ratio.")

    # Trend / momentum conditions
    require_trend          = models.BooleanField(default=True)
    require_volume_spike   = models.BooleanField(default=False)
    min_rsi                = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    max_rsi                = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    min_confidence_score   = models.DecimalField(max_digits=5, decimal_places=2, default=60,
                                                  help_text="Minimum score to be listed as a candidate.")

    # Schedule
    scan_interval_seconds  = models.PositiveIntegerField(default=60)
    is_active              = models.BooleanField(default=True)

    # Which exchanges to include in scans (list of exchange slugs)
    enabled_exchanges = models.JSONField(default=list, help_text='e.g. ["binance", "bybit"]')

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Scanner Settings"
        verbose_name_plural = "Scanner Settings"

    def __str__(self) -> str:
        return f"ScannerSettings(user={self.user_id}, active={self.is_active})"
