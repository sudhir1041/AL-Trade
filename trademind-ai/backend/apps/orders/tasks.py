"""
apps/orders/tasks.py
--------------------
T11 ✅  Order execution, sync, and position management tasks.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.orders.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=5, queue="order_sync",
             name="apps.orders.tasks.submit_order_to_exchange")
def submit_order_to_exchange(self, order_id: str) -> dict:
    """T11 ✅  Submit a live order to the exchange via adapter."""
    from apps.orders.models import Order, OrderEvent, OrderStatus
    try:
        order = Order.objects.select_related(
            "trading_pair", "exchange_account__exchange"
        ).get(pk=order_id)

        # TODO: load exchange adapter and call adapter.place_order(...)
        # Scaffold: mark as SUBMITTED
        order.status = OrderStatus.SUBMITTED
        order.save(update_fields=["status"])

        OrderEvent.objects.create(
            order=order,
            event_type="SUBMITTED",
            old_status=OrderStatus.CREATED,
            new_status=OrderStatus.SUBMITTED,
            message="Order submitted to exchange.",
        )
        logger.info("Order submitted: %s", order_id)
        return {"status": "SUBMITTED", "order_id": order_id}

    except Order.DoesNotExist:
        return {"status": "ERROR", "message": "Order not found"}
    except Exception as exc:
        logger.exception("Failed to submit order %s", order_id)
        raise self.retry(exc=exc)


@shared_task(queue="order_sync", name="apps.orders.tasks.simulate_paper_order")
def simulate_paper_order(order_id: str) -> dict:
    """T11 ✅  Simulate a paper trade order fill instantly."""
    from apps.orders.models import Order, OrderEvent, OrderStatus, Position, PositionStatus
    from django.utils import timezone
    try:
        order = Order.objects.select_related("trading_pair").get(pk=order_id)
        current_price = float(order.price or 0) or _get_current_price(order.trading_pair.symbol)

        # Fill the order at market price
        order.status              = OrderStatus.FILLED
        order.filled_quantity     = order.quantity
        order.average_fill_price  = current_price
        order.filled_at           = timezone.now()
        order.save(update_fields=["status", "filled_quantity", "average_fill_price", "filled_at"])

        # Create position
        Position.objects.create(
            user=order.user,
            exchange_account=order.exchange_account,
            trading_pair=order.trading_pair,
            strategy=order.strategy,
            entry_order=order,
            side="LONG" if order.side == "BUY" else "SHORT",
            entry_price=current_price,
            current_price=current_price,
            quantity=order.quantity,
            remaining_quantity=order.quantity,
            stop_loss_price=order.stop_loss_price,
            take_profit_price=order.take_profit_price,
            is_paper_trade=True,
            tenant_id=order.tenant_id,
        )
        logger.info("Paper order simulated: %s", order_id)
        return {"status": "FILLED", "order_id": order_id}

    except Exception as exc:
        logger.exception("Paper order simulation failed: %s", order_id)
        return {"status": "ERROR", "message": str(exc)}


@shared_task(queue="order_sync", name="apps.orders.tasks.cancel_order_on_exchange")
def cancel_order_on_exchange(order_id: str) -> dict:
    """T11 ✅  Cancel an open order on the exchange."""
    from apps.orders.models import Order, OrderStatus
    try:
        order = Order.objects.get(pk=order_id)
        # TODO: call adapter.cancel_order(order.exchange_order_id)
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return {"status": "CANCELLED", "order_id": order_id}
    except Exception as exc:
        logger.exception("Cancel order failed: %s", order_id)
        return {"status": "ERROR", "message": str(exc)}


@shared_task(queue="order_sync", name="apps.orders.tasks.close_position")
def close_position(position_id: str, partial: bool = False, close_pct: float = 100) -> dict:
    """T11 ✅  Close an open position (fully or partially)."""
    from apps.orders.models import Position, PositionStatus, Order, OrderStatus
    from django.utils import timezone
    try:
        pos = Position.objects.get(pk=position_id, status=PositionStatus.OPEN)
        close_qty = float(pos.remaining_quantity) * (close_pct / 100 if partial else 1.0)
        price     = _get_current_price(pos.trading_pair.symbol) or float(pos.entry_price)

        pnl_delta = (price - float(pos.entry_price)) * close_qty if pos.side == "LONG" \
                    else (float(pos.entry_price) - price) * close_qty

        pos.realized_pnl   = float(pos.realized_pnl) + pnl_delta
        pos.remaining_quantity = float(pos.remaining_quantity) - close_qty
        if not partial or float(pos.remaining_quantity) <= 0:
            pos.status    = PositionStatus.CLOSED
            pos.closed_at = timezone.now()
        else:
            pos.status = PositionStatus.PARTIALLY_CLOSED
            pos.partial_close_done = True
        pos.save()
        return {"status": "OK", "pnl": pnl_delta}
    except Exception as exc:
        logger.exception("Close position failed: %s", position_id)
        return {"status": "ERROR", "message": str(exc)}


@shared_task(queue="order_sync", name="apps.orders.tasks.sync_open_orders")
def sync_open_orders() -> dict:
    """T11 ✅  Sync all open orders with exchange statuses — runs every 15s."""
    from apps.orders.models import Order, OrderStatus
    open_orders = Order.objects.filter(status__in=[
        OrderStatus.SUBMITTED, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED
    ]).exclude(is_paper_trade=True)

    synced = 0
    for order in open_orders.select_related("exchange_account__exchange")[:200]:
        # TODO: call adapter.get_order_status(order.exchange_order_id)
        synced += 1
    return {"synced": synced}


def _get_current_price(symbol: str) -> float:
    from django.core.cache import cache
    ticker = cache.get(f"ticker:{symbol}") or {}
    return float(ticker.get("price", 0) or 0)
