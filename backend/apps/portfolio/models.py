"""
apps/portfolio/models.py
------------------------
Portfolio Management models – balances, asset allocation, PnL history.
"""

import uuid

from django.db import models

from core.models import TenantBaseModel


class Portfolio(TenantBaseModel):
    """
    Aggregate portfolio snapshot for a user's exchange account.
    Updated by the portfolio sync worker every 30 seconds.
    """

    user             = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="portfolios")
    exchange_account = models.ForeignKey("exchanges.ExchangeAccount", on_delete=models.CASCADE,
                                          related_name="portfolio")

    # Balances (in quote asset, typically USDT)
    total_balance      = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    available_balance  = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    locked_balance     = models.DecimalField(max_digits=24, decimal_places=8, default=0,
                                              help_text="Balance locked in open orders/positions.")

    # PnL
    unrealized_pnl     = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    realized_pnl       = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    total_pnl          = models.DecimalField(max_digits=24, decimal_places=8, default=0)

    # Performance since start
    initial_balance    = models.DecimalField(max_digits=24, decimal_places=8, default=0,
                                              help_text="Balance when the portfolio was first connected.")
    peak_balance       = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    max_drawdown_pct   = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Metadata
    last_synced_at     = models.DateTimeField(null=True, blank=True)
    is_paper           = models.BooleanField(default=False)

    class Meta(TenantBaseModel.Meta):
        verbose_name        = "Portfolio"
        verbose_name_plural = "Portfolios"
        unique_together     = [("user", "exchange_account")]
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"Portfolio(user={self.user_id}, balance={self.total_balance})"

    @property
    def return_pct(self) -> float:
        """Overall portfolio return percentage from initial balance."""
        if not self.initial_balance:
            return 0.0
        return float((self.total_balance - self.initial_balance) / self.initial_balance * 100)


class PortfolioAsset(models.Model):
    """
    Individual asset holding within a portfolio snapshot.
    One row per asset per portfolio, overwritten on each sync.
    """

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio      = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="assets")
    asset          = models.CharField(max_length=20, db_index=True)
    quantity       = models.DecimalField(max_digits=24, decimal_places=8)
    avg_buy_price  = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    current_price  = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    value_usdt     = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    allocation_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                          help_text="% of total portfolio value.")
    unrealized_pnl = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    unrealized_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Portfolio Asset"
        verbose_name_plural = "Portfolio Assets"
        unique_together     = [("portfolio", "asset")]
        ordering            = ["-value_usdt"]

    def __str__(self) -> str:
        return f"{self.asset}: {self.quantity} @ {self.current_price} ({self.allocation_pct}%)"


class PnLHistory(models.Model):
    """
    Daily PnL snapshots for charting and reporting.
    One row per user per exchange_account per date.
    """

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user             = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="pnl_history")
    exchange_account = models.ForeignKey("exchanges.ExchangeAccount", on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="pnl_history")
    date             = models.DateField(db_index=True)
    daily_pnl        = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    cumulative_pnl   = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    portfolio_value  = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    trade_count      = models.PositiveIntegerField(default=0)
    win_count        = models.PositiveIntegerField(default=0)
    loss_count       = models.PositiveIntegerField(default=0)
    win_rate_pct     = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name        = "PnL History"
        verbose_name_plural = "PnL History"
        unique_together     = [("user", "exchange_account", "date")]
        ordering            = ["-date"]
        indexes = [
            models.Index(fields=["user", "-date"]),
        ]

    def __str__(self) -> str:
        return f"PnL(user={self.user_id}, date={self.date}, daily={self.daily_pnl})"


class PortfolioHistory(models.Model):
    """
    Hourly balance snapshots for performance charting.
    """

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio        = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="history")
    total_balance    = models.DecimalField(max_digits=24, decimal_places=8)
    unrealized_pnl   = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    recorded_at      = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name        = "Portfolio History"
        verbose_name_plural = "Portfolio History"
        ordering            = ["-recorded_at"]
        indexes = [
            models.Index(fields=["portfolio", "-recorded_at"]),
        ]

    def __str__(self) -> str:
        return f"PortfolioHistory(balance={self.total_balance}, at={self.recorded_at})"
