"""
apps/market/models.py
---------------------
Market-data models for TradeMind AI.

Models
------
- TradingPair   : Exchange-specific trading pair metadata
- Ticker        : Latest price snapshot
- OHLCV         : Candlestick data at various timeframes
- FundingRate   : Perpetual futures funding rate
- OpenInterest  : Open interest for futures contracts
- Liquidation   : Liquidation event records
"""

import uuid

from django.db import models

from apps.exchanges.models import Exchange


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Timeframe(models.TextChoices):
    M1  = "1m",  "1 Minute"
    M5  = "5m",  "5 Minutes"
    M15 = "15m", "15 Minutes"
    H1  = "1h",  "1 Hour"
    H4  = "4h",  "4 Hours"
    D1  = "1d",  "1 Day"


# ---------------------------------------------------------------------------
# TradingPair
# ---------------------------------------------------------------------------

class TradingPair(models.Model):
    """Exchange-specific trading pair with instrument metadata."""

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange      = models.ForeignKey(
        Exchange,
        on_delete=models.CASCADE,
        related_name="trading_pairs",
        verbose_name="Exchange",
    )
    symbol        = models.CharField(max_length=30, verbose_name="Symbol",
                                     help_text="e.g. BTCUSDT, ETH-PERP")
    base_asset    = models.CharField(max_length=20, verbose_name="Base Asset")
    quote_asset   = models.CharField(max_length=20, verbose_name="Quote Asset")
    is_active     = models.BooleanField(default=True,  verbose_name="Active")
    is_futures    = models.BooleanField(default=False, verbose_name="Futures Contract")
    # Lot-size filters
    min_quantity  = models.DecimalField(max_digits=30, decimal_places=8,
                                        null=True, blank=True, verbose_name="Min Quantity")
    max_quantity  = models.DecimalField(max_digits=30, decimal_places=8,
                                        null=True, blank=True, verbose_name="Max Quantity")
    quantity_step = models.DecimalField(max_digits=30, decimal_places=8,
                                        null=True, blank=True, verbose_name="Quantity Step")
    price_step    = models.DecimalField(max_digits=30, decimal_places=8,
                                        null=True, blank=True, verbose_name="Price Step")
    min_notional  = models.DecimalField(max_digits=30, decimal_places=8,
                                        null=True, blank=True, verbose_name="Min Notional")
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Trading Pair"
        verbose_name_plural = "Trading Pairs"
        ordering            = ["exchange", "symbol"]
        unique_together     = [("exchange", "symbol")]
        indexes = [
            models.Index(fields=["symbol", "is_active"]),
            models.Index(fields=["exchange", "is_futures"]),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} @ {self.exchange}"

class Ticker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name="tickers")
    price = models.DecimalField(max_digits=20, decimal_places=8)
    bid = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ask = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    high_24h = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    low_24h = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    change_24h_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class OHLCV(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name="ohlcv")
    timeframe = models.CharField(max_length=10, choices=Timeframe.choices)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)

class FundingRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name="funding_rates")
    rate = models.DecimalField(max_digits=10, decimal_places=6)
    timestamp = models.DateTimeField()

class OpenInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name="open_interests")
    value = models.DecimalField(max_digits=30, decimal_places=8)
    timestamp = models.DateTimeField()

class Liquidation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name="liquidations")
    side = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=30, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    timestamp = models.DateTimeField()
