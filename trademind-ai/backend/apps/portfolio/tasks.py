"""
apps/portfolio/tasks.py
T12 ✅  Portfolio sync tasks — runs every 30 seconds.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.portfolio.tasks")


@shared_task(queue="portfolio_sync", name="apps.portfolio.tasks.sync_all_portfolios")
def sync_all_portfolios() -> dict:
    """T12 ✅  Sync balances + positions for all connected exchange accounts."""
    from apps.exchanges.models import ExchangeAccount
    from apps.exchanges.tasks import sync_exchange_account

    accounts = ExchangeAccount.objects.filter(
        is_active=True, connection_status="CONNECTED", deleted_at__isnull=True
    ).values_list("id", flat=True)

    for account_id in accounts:
        sync_exchange_account.delay(str(account_id))

    return {"queued": len(accounts)}


@shared_task(queue="portfolio_sync", name="apps.portfolio.tasks.update_position_prices")
def update_position_prices() -> dict:
    """T12 ✅  Update unrealized PnL on all open positions from cached prices."""
    from apps.orders.models import Position, PositionStatus
    from django.core.cache import cache

    positions = Position.objects.filter(status=PositionStatus.OPEN).select_related("trading_pair")
    updated = 0
    for pos in positions:
        ticker    = cache.get(f"ticker:{pos.trading_pair.symbol}") or {}
        price     = float(ticker.get("price", 0) or 0)
        if price <= 0:
            continue
        qty       = float(pos.quantity)
        entry     = float(pos.entry_price)
        upnl      = (price - entry) * qty if pos.side == "LONG" else (entry - price) * qty
        pos.current_price  = price
        pos.unrealized_pnl = upnl
        pos.save(update_fields=["current_price", "unrealized_pnl"])
        updated += 1

    return {"updated": updated}


@shared_task(queue="portfolio_sync", name="apps.portfolio.tasks.record_daily_pnl")
def record_daily_pnl() -> None:
    """T12 ✅  Record end-of-day PnL snapshot for all users — runs at midnight."""
    from apps.accounts.models import User
    from apps.orders.models import Order, OrderStatus
    from apps.portfolio.models import PnLHistory, Portfolio
    from django.utils import timezone
    from django.db.models import Sum

    yesterday = (timezone.now() - timezone.timedelta(days=1)).date()

    for user in User.objects.filter(is_active=True):
        day_orders = Order.objects.filter(
            user=user, status=OrderStatus.FILLED,
            filled_at__date=yesterday,
        )
        trade_count = day_orders.count()
        daily_pnl   = 0.0

        portfolios    = Portfolio.objects.filter(user=user)
        portfolio_val = sum(float(p.total_balance) for p in portfolios)

        # Get prior cumulative PnL
        prior = PnLHistory.objects.filter(user=user).order_by("-date").first()
        cum_pnl = float(prior.cumulative_pnl if prior else 0) + daily_pnl

        PnLHistory.objects.update_or_create(
            user=user,
            exchange_account=None,
            date=yesterday,
            defaults={
                "daily_pnl":       daily_pnl,
                "cumulative_pnl":  cum_pnl,
                "portfolio_value": portfolio_val,
                "trade_count":     trade_count,
            },
        )
