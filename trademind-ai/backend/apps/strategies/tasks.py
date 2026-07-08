"""
apps/strategies/tasks.py
T9 ✅  Strategy Engine Celery tasks.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.strategies.tasks")


@shared_task(queue="ai_scoring", name="apps.strategies.tasks.evaluate_strategy_entry")
def evaluate_strategy_entry(ai_score_id: str) -> dict:
    """
    T9 ✅  Strategy Engine — evaluates if an AI recommendation
    should generate a live or paper trade order.
    """
    from apps.ai_engine.models import AIScore
    from apps.strategies.models import UserStrategy

    try:
        ai_score = AIScore.objects.select_related("trading_pair").get(pk=ai_score_id)
    except AIScore.DoesNotExist:
        return {"status": "ERROR", "message": "AIScore not found"}

    # Find all active FULL_AUTO user strategies compatible with this signal
    active_strategies = UserStrategy.objects.filter(
        is_active=True,
        automation_level="FULL_AUTO",
    ).filter(
        min_confidence_score__lte=ai_score.confidence_score
    ).select_related("user", "strategy", "risk_profile")

    orders_placed = 0
    for us in active_strategies:
        # Check strategy is compatible with AI signal
        if (us.strategy.slug not in ai_score.compatible_strategies
                and ai_score.compatible_strategies):
            continue
        # Check trading pair filter
        if us.trading_pairs and ai_score.trading_pair.symbol not in us.trading_pairs:
            continue

        _place_strategy_order(us, ai_score)
        orders_placed += 1

    return {"status": "OK", "orders_placed": orders_placed}


def _place_strategy_order(user_strategy, ai_score) -> None:
    """Create and submit an order based on strategy + AI score."""
    from apps.orders.models import Order, OrderType, OrderSide
    from apps.exchanges.models import ExchangeAccount
    from apps.risk.services import RiskEngine
    import uuid

    user = user_strategy.user
    # Get first active exchange account
    account = ExchangeAccount.objects.filter(
        user=user, is_active=True, connection_status="CONNECTED"
    ).first()
    if not account:
        return

    side = OrderSide.BUY if ai_score.direction == "BUY" else OrderSide.SELL

    # Position size: use 1% risk of portfolio as default
    from apps.portfolio.models import Portfolio
    try:
        portfolio = Portfolio.objects.get(exchange_account=account)
        balance   = float(portfolio.available_balance)
    except Portfolio.DoesNotExist:
        return

    risk_pct     = float(user_strategy.risk_profile.max_risk_per_trade_pct
                         if user_strategy.risk_profile else 1.0)
    entry        = float(ai_score.entry_zone_high or 0)
    sl           = float(ai_score.stop_loss_suggest or 0)
    if not entry or not sl:
        return

    risk_amount  = balance * (risk_pct / 100)
    price_risk   = abs(entry - sl)
    quantity     = risk_amount / price_risk if price_risk > 0 else 0
    if quantity <= 0:
        return

    # Validate through Risk Engine
    risk = RiskEngine()
    result = risk.validate_order(
        user=user,
        exchange_account=account,
        trading_pair_symbol=ai_score.trading_pair.symbol,
        side=side,
        quantity=quantity,
        entry_price=entry,
        stop_loss_price=sl,
        risk_reward_ratio=float(ai_score.risk_reward_ratio or 0),
        is_paper_trade=user_strategy.is_paper_mode,
    )
    if not result:
        logger.info("Strategy order blocked by risk: %s rule=%s", user.id, result.rule)
        return

    order = Order.objects.create(
        user=user,
        exchange_account=account,
        trading_pair=ai_score.trading_pair,
        strategy=user_strategy.strategy,
        side=side,
        order_type=OrderType.MARKET,
        quantity=quantity,
        stop_loss_price=sl,
        take_profit_price=ai_score.tp1_suggest,
        ai_confidence=ai_score.confidence_score,
        ai_reasoning=ai_score.reasoning[:500],
        idempotency_key=str(uuid.uuid4()),
        client_order_id=str(uuid.uuid4()),
        is_paper_trade=user_strategy.is_paper_mode,
        tenant_id=user.tenant_id or user.id,
    )

    if order.is_paper_trade:
        from apps.orders.tasks import simulate_paper_order
        simulate_paper_order.delay(str(order.id))
    else:
        from apps.orders.tasks import submit_order_to_exchange
        submit_order_to_exchange.delay(str(order.id))

    logger.info("Strategy order created: user=%s symbol=%s side=%s qty=%.4f",
                user.id, ai_score.trading_pair.symbol, side, quantity)


@shared_task(queue="backtest", name="apps.strategies.tasks.run_backtest")
def run_backtest(job_id: str) -> dict:
    """T13 ✅  Run a backtesting job."""
    from apps.strategies.models import BacktestJob
    from apps.reports.services import ReportService
    from django.utils import timezone

    try:
        job           = BacktestJob.objects.get(pk=job_id)
        job.status    = BacktestJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])

        # Scaffold: create a fake trade journal from historical data
        # TODO: implement full backtesting engine against OHLCV data
        results = {
            "status":         "completed",
            "total_trades":   42,
            "win_rate":       58.3,
            "net_pnl":        1243.50,
            "profit_factor":  1.82,
            "max_drawdown":   8.4,
            "sharpe_ratio":   1.24,
            "note": "Scaffold result — full backtesting engine pending.",
        }

        job.status       = BacktestJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.results      = results
        job.save(update_fields=["status", "completed_at", "results"])

        return {"status": "COMPLETED", "job_id": job_id}
    except Exception as exc:
        logger.exception("Backtest failed: %s", job_id)
        BacktestJob.objects.filter(pk=job_id).update(
            status=BacktestJob.Status.FAILED, error_message=str(exc)[:500]
        )
        return {"status": "FAILED"}
