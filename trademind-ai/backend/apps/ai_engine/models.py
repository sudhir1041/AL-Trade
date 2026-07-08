"""
apps/ai_engine/models.py
------------------------
AI Decision Engine models – predictions, confidence scores, recommendations,
market regime classifications, and learning dataset.

The AI engine NEVER submits orders directly.
It only produces recommendations consumed by the Strategy Engine.
"""

import uuid

from django.db import models

from core.models import TenantBaseModel


class RecommendationDirection(models.TextChoices):
    BUY    = "BUY",    "Buy"
    SELL   = "SELL",   "Sell"
    HOLD   = "HOLD",   "Hold"
    IGNORE = "IGNORE", "Ignore"


class MarketRegimeType(models.TextChoices):
    STRONG_BULL  = "STRONG_BULL",  "Strong Bull Trend"
    WEAK_BULL    = "WEAK_BULL",    "Weak Bull Trend"
    STRONG_BEAR  = "STRONG_BEAR",  "Strong Bear Trend"
    WEAK_BEAR    = "WEAK_BEAR",    "Weak Bear Trend"
    SIDEWAYS     = "SIDEWAYS",     "Sideways Range"
    HIGH_VOL     = "HIGH_VOL",     "High Volatility"
    LOW_VOL      = "LOW_VOL",      "Low Volatility"
    NEWS_DRIVEN  = "NEWS_DRIVEN",  "News-Driven Market"


class RiskLevel(models.TextChoices):
    LOW    = "LOW",    "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH   = "HIGH",   "High"
    EXTREME = "EXTREME", "Extreme"


# ---------------------------------------------------------------------------
# AI Score (per symbol, per scan cycle)
# ---------------------------------------------------------------------------

class AIScore(models.Model):
    """
    The AI engine's evaluation output for a single trading pair.
    Produced after running all 9 pipeline stages.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair    = models.ForeignKey("market.TradingPair", on_delete=models.CASCADE,
                                         related_name="ai_scores")

    # Core scores (0–100)
    confidence_score  = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                             help_text="Overall opportunity quality score (0–100).")
    risk_score        = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                             help_text="Risk level score (0=low risk, 100=extreme risk).")
    momentum_score    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    volume_score      = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    trend_score       = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    structure_score   = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Recommendation
    direction         = models.CharField(max_length=10, choices=RecommendationDirection.choices,
                                          default=RecommendationDirection.IGNORE)
    risk_level        = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    market_regime     = models.CharField(max_length=20, choices=MarketRegimeType.choices, blank=True)

    # Entry/exit suggestions
    entry_zone_low    = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    entry_zone_high   = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_loss_suggest = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    tp1_suggest       = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    tp2_suggest       = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    tp3_suggest       = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    risk_reward_ratio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Explainability
    supporting_factors = models.JSONField(default=list,
                                           help_text="List of factor names that contributed positively.")
    conflicting_factors = models.JSONField(default=list,
                                            help_text="List of factor names that reduced confidence.")
    reasoning          = models.TextField(blank=True, help_text="Human-readable explanation.")

    # Multi-timeframe summary
    mtf_alignment = models.JSONField(default=dict,
                                      help_text='e.g. {"5m":"BULLISH","15m":"BULLISH","1h":"SIDEWAYS"}')

    # Strategy compatibility
    compatible_strategies = models.JSONField(default=list,
                                              help_text="Strategy slugs compatible with this setup.")

    # Metadata
    timeframe    = models.CharField(max_length=10, default="1h")
    is_automated = models.BooleanField(default=False,
                                        help_text="True if this score triggered an automated trade.")
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "AI Score"
        verbose_name_plural = "AI Scores"
        ordering            = ["-confidence_score"]
        indexes = [
            models.Index(fields=["trading_pair", "-created_at"]),
            models.Index(fields=["direction", "-created_at"]),
            models.Index(fields=["confidence_score", "direction"]),
        ]

    def __str__(self) -> str:
        return (
            f"AIScore({self.trading_pair} → {self.direction}, "
            f"conf={self.confidence_score}, regime={self.market_regime})"
        )

    @property
    def is_tradeable(self) -> bool:
        """Return True if score meets the 90+ automation threshold."""
        return float(self.confidence_score) >= 90 and self.direction in (
            RecommendationDirection.BUY, RecommendationDirection.SELL
        )


# ---------------------------------------------------------------------------
# AI Learning Dataset
# ---------------------------------------------------------------------------

class AILearningRecord(models.Model):
    """
    Stores outcomes of recommendations for continuous model improvement.
    Appended when a trade closes. Used as training data for ML models.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_score        = models.ForeignKey(AIScore, on_delete=models.SET_NULL, null=True,
                                         related_name="learning_records")
    trading_pair    = models.ForeignKey("market.TradingPair", on_delete=models.CASCADE)

    # What the AI recommended
    recommendation  = models.CharField(max_length=10, choices=RecommendationDirection.choices)
    confidence_at_signal = models.DecimalField(max_digits=5, decimal_places=2)
    risk_level_at_signal = models.CharField(max_length=10, choices=RiskLevel.choices)
    market_regime_at_signal = models.CharField(max_length=20, choices=MarketRegimeType.choices, blank=True)

    # What happened
    was_executed    = models.BooleanField(default=False, help_text="Did the user execute this trade?")
    trade_outcome   = models.CharField(
        max_length=10,
        choices=[("WIN", "Win"), ("LOSS", "Loss"), ("BREAKEVEN", "Breakeven"), ("SKIPPED", "Skipped")],
        blank=True,
    )
    actual_pnl_pct  = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    strategy_used   = models.CharField(max_length=50, blank=True)

    # Feature snapshot (for retraining)
    feature_snapshot = models.JSONField(default=dict,
                                         help_text="All indicator values at signal time.")

    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "AI Learning Record"
        verbose_name_plural = "AI Learning Records"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["trading_pair", "-created_at"]),
            models.Index(fields=["recommendation", "trade_outcome"]),
        ]

    def __str__(self) -> str:
        return (
            f"AILearning({self.trading_pair}, rec={self.recommendation}, "
            f"outcome={self.trade_outcome})"
        )


# ---------------------------------------------------------------------------
# Market Regime Detection
# ---------------------------------------------------------------------------

class MarketRegimeSnapshot(models.Model):
    """
    Periodic market-wide regime classification.
    Used by the Strategy Engine to enable/disable strategies.
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    regime        = models.CharField(max_length=20, choices=MarketRegimeType.choices, db_index=True)
    btc_trend     = models.CharField(max_length=20, blank=True)
    eth_trend     = models.CharField(max_length=20, blank=True)
    dominance_btc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fear_greed_index = models.PositiveSmallIntegerField(null=True, blank=True,
                                                         help_text="0-100 Fear & Greed Index value.")
    factors       = models.JSONField(default=dict)
    recorded_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Market Regime Snapshot"
        verbose_name_plural = "Market Regime Snapshots"
        ordering            = ["-recorded_at"]

    def __str__(self) -> str:
        return f"Regime({self.regime}, BTC={self.btc_trend}, at={self.recorded_at})"
