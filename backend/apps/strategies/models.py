"""
apps/strategies/models.py
-------------------------
Strategy Engine models – built-in strategies, user configurations,
assignments, performance tracking, and custom strategies.
"""

import uuid

from django.db import models

from core.models import TenantBaseModel


class StrategyType(models.TextChoices):
    TREND_FOLLOWING = "TREND_FOLLOWING", "Trend Following"
    BREAKOUT        = "BREAKOUT",        "Breakout"
    PULLBACK        = "PULLBACK",        "Pullback"
    MOMENTUM        = "MOMENTUM",        "Momentum"
    SWING           = "SWING",           "Swing Trading"
    SCALPING        = "SCALPING",        "Scalping"
    GRID            = "GRID",            "Grid Trading"
    DCA             = "DCA",             "Dollar Cost Averaging"
    MEAN_REVERSION  = "MEAN_REVERSION",  "Mean Reversion"
    NEWS_REACTION   = "NEWS_REACTION",   "News Reaction"
    SMC             = "SMC",             "Smart Money Concepts"
    ICT             = "ICT",             "ICT Concepts"
    CUSTOM          = "CUSTOM",          "Custom Strategy"


class AutomationLevel(models.TextChoices):
    MANUAL      = "MANUAL",      "Manual (Signals Only)"
    SEMI_AUTO   = "SEMI_AUTO",   "Semi-Automatic (Confirm Before Execute)"
    FULL_AUTO   = "FULL_AUTO",   "Fully Automatic"


class MarketRegime(models.TextChoices):
    STRONG_BULL  = "STRONG_BULL",  "Strong Bull"
    WEAK_BULL    = "WEAK_BULL",    "Weak Bull"
    STRONG_BEAR  = "STRONG_BEAR",  "Strong Bear"
    WEAK_BEAR    = "WEAK_BEAR",    "Weak Bear"
    SIDEWAYS     = "SIDEWAYS",     "Sideways Range"
    HIGH_VOL     = "HIGH_VOL",     "High Volatility"
    LOW_VOL      = "LOW_VOL",      "Low Volatility"
    NEWS_DRIVEN  = "NEWS_DRIVEN",  "News-Driven"


# ---------------------------------------------------------------------------
# Strategy (platform-level definition)
# ---------------------------------------------------------------------------

class Strategy(models.Model):
    """
    Platform-level strategy definition.
    These are the built-in strategies available to all users.
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length=100, unique=True)
    slug          = models.SlugField(max_length=100, unique=True)
    strategy_type = models.CharField(max_length=30, choices=StrategyType.choices)
    description   = models.TextField(blank=True)

    # Which market regimes this strategy is suitable for
    suitable_regimes  = models.JSONField(
        default=list,
        help_text='List of MarketRegime values. e.g. ["STRONG_BULL", "WEAK_BULL"]',
    )
    unsuitable_regimes = models.JSONField(default=list)

    # Minimum timeframe required
    min_timeframe   = models.CharField(max_length=10, default="5m")
    max_timeframe   = models.CharField(max_length=10, default="1d")

    # Configuration schema (used to render the config UI)
    config_schema   = models.JSONField(default=dict, help_text="JSON Schema for user configuration options.")

    # Default parameters
    default_params  = models.JSONField(default=dict)

    is_active       = models.BooleanField(default=True)
    requires_premium = models.BooleanField(default=False)
    sort_order      = models.PositiveSmallIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Strategy"
        verbose_name_plural = "Strategies"
        ordering            = ["sort_order", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.strategy_type})"


# ---------------------------------------------------------------------------
# UserStrategy (user's configured instance of a strategy)
# ---------------------------------------------------------------------------

class UserStrategy(TenantBaseModel):
    """
    A user's configured and activated instance of a platform Strategy.
    Users can have multiple configurations of the same strategy type.
    """

    user           = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="user_strategies")
    strategy       = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="user_instances")
    name           = models.CharField(max_length=100, help_text="User-defined name for this configuration.")

    # Configuration
    parameters     = models.JSONField(default=dict, help_text="User overrides for strategy parameters.")
    timeframes     = models.JSONField(default=list, help_text='e.g. ["5m","15m","1h"]')
    trading_pairs  = models.JSONField(default=list, help_text="Specific pairs to trade, empty = use scanner.")
    exchanges      = models.JSONField(default=list, help_text="Exchange account IDs to use.")

    # Execution settings
    automation_level      = models.CharField(max_length=20, choices=AutomationLevel.choices,
                                              default=AutomationLevel.SEMI_AUTO)
    min_confidence_score  = models.DecimalField(max_digits=5, decimal_places=2, default=70,
                                                 help_text="Minimum AI confidence to execute a trade.")
    max_trades_per_day    = models.PositiveSmallIntegerField(default=10)
    trading_sessions      = models.JSONField(default=list,
                                              help_text='e.g. [{"start":"09:00","end":"17:00","timezone":"UTC"}]')

    # Risk profile to use
    risk_profile   = models.ForeignKey("risk.RiskProfile", on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="user_strategies")

    # Status
    is_active      = models.BooleanField(default=True, db_index=True)
    is_paper_mode  = models.BooleanField(default=False, help_text="If True, only paper trades.")

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "User Strategy"
        verbose_name_plural = "User Strategies"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"UserStrategy({self.name}, user={self.user_id}, active={self.is_active})"


# ---------------------------------------------------------------------------
# Strategy Performance
# ---------------------------------------------------------------------------

class StrategyPerformance(TenantBaseModel):
    """
    Aggregated performance metrics for a UserStrategy.
    Updated after each trade closes.
    """

    user_strategy   = models.OneToOneField(UserStrategy, on_delete=models.CASCADE,
                                             related_name="performance")
    user            = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                                         related_name="strategy_performances")

    # Trade counts
    total_trades    = models.PositiveIntegerField(default=0)
    winning_trades  = models.PositiveIntegerField(default=0)
    losing_trades   = models.PositiveIntegerField(default=0)

    # Win/loss metrics
    win_rate_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_win_usdt    = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    avg_loss_usdt   = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    profit_factor   = models.DecimalField(max_digits=8, decimal_places=4, default=0,
                                           help_text="Gross profit / Gross loss")

    # PnL
    total_pnl_usdt       = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_commission_usdt = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    net_pnl_usdt         = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # Risk-adjusted metrics
    sharpe_ratio    = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    sortino_ratio   = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    calmar_ratio    = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    max_drawdown_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    recovery_factor  = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    # Holding time
    avg_holding_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Tracking
    first_trade_at  = models.DateTimeField(null=True, blank=True)
    last_trade_at   = models.DateTimeField(null=True, blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Strategy Performance"
        verbose_name_plural = "Strategy Performances"

    def __str__(self) -> str:
        return f"Performance({self.user_strategy.name}, win={self.win_rate_pct}%, pnl={self.net_pnl_usdt})"


# ---------------------------------------------------------------------------
# Backtest Job
# ---------------------------------------------------------------------------

class BacktestJob(TenantBaseModel):
    """Records a strategy backtesting run."""

    class Status(models.TextChoices):
        QUEUED    = "QUEUED",    "Queued"
        RUNNING   = "RUNNING",   "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED    = "FAILED",    "Failed"

    user          = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="backtest_jobs")
    strategy      = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="backtest_jobs")
    parameters    = models.JSONField(default=dict)
    trading_pair  = models.ForeignKey("market.TradingPair", on_delete=models.SET_NULL,
                                       null=True, related_name="backtest_jobs")
    timeframe     = models.CharField(max_length=10, default="1h")
    start_date    = models.DateField()
    end_date      = models.DateField()
    initial_balance = models.DecimalField(max_digits=20, decimal_places=2, default=10000)

    status        = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    results       = models.JSONField(default=dict, help_text="Backtest result summary.")
    started_at    = models.DateTimeField(null=True, blank=True)
    completed_at  = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Backtest Job"
        verbose_name_plural = "Backtest Jobs"
        ordering            = ["-created_at"]

    def __str__(self) -> str:
        return f"Backtest({self.strategy.name}, {self.trading_pair}, {self.status})"
