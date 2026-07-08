"""
apps/notifications/services.py
--------------------------------
T14 ✅  Notification Service — creates and dispatches notifications
across all configured channels (Email, Telegram, WhatsApp, Push, Discord, Slack).
"""
import logging
from typing import Any

logger = logging.getLogger("trademind.notifications.services")


class NotificationService:
    """
    Creates a Notification record and queues delivery tasks for
    every channel the user has enabled for this event type.
    """

    def send(
        self,
        user,
        event_type: str,
        title: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        """
        T14 ✅  Main entry point. Creates DB record and enqueues delivery.
        """
        from apps.notifications.models import (
            Notification, NotificationDelivery, DeliveryStatus
        )
        from apps.users.models import UserPreferences

        try:
            prefs = UserPreferences.objects.get(user=user)
        except UserPreferences.DoesNotExist:
            prefs = None

        notif = Notification.objects.create(
            user=user,
            tenant_id=user.tenant_id or user.id,
            event_type=event_type,
            title=title,
            message=message,
            payload=payload or {},
        )

        channels = self._get_enabled_channels(user, prefs, event_type)
        for channel in channels:
            NotificationDelivery.objects.create(
                notification=notif,
                channel=channel,
                status=DeliveryStatus.PENDING,
            )
            from apps.notifications.tasks import deliver_notification
            deliver_notification.delay(str(notif.id), channel)

    def _get_enabled_channels(self, user, prefs, event_type: str) -> list[str]:
        """Return list of channels enabled by user preferences."""
        if not prefs:
            return ["EMAIL"]   # fallback to email only

        channels = []
        if prefs.notification_email:
            channels.append("EMAIL")
        if prefs.notification_telegram and prefs.telegram_chat_id:
            channels.append("TELEGRAM")
        if prefs.notification_push:
            channels.append("PUSH")
        if prefs.notification_discord and prefs.discord_webhook:
            channels.append("DISCORD")
        if prefs.notification_slack and prefs.slack_webhook:
            channels.append("SLACK")
        return channels


# ── Convenience helpers ───────────────────────────────────────────────────────

def notify_trade_executed(user, order) -> None:
    """T14 ✅"""
    NotificationService().send(
        user=user,
        event_type="TRADE_EXECUTED",
        title=f"Trade Executed: {order.side} {order.trading_pair.symbol}",
        message=(
            f"{order.side} {order.quantity} {order.trading_pair.symbol} "
            f"filled at {order.average_fill_price}."
        ),
        payload={"order_id": str(order.id), "symbol": order.trading_pair.symbol},
    )


def notify_position_closed(user, position) -> None:
    """T14 ✅"""
    pnl_sign = "+" if float(position.realized_pnl) >= 0 else ""
    NotificationService().send(
        user=user,
        event_type="POSITION_CLOSED",
        title=f"Position Closed: {position.trading_pair.symbol}",
        message=(
            f"{position.side} {position.trading_pair.symbol} closed. "
            f"PnL: {pnl_sign}{position.realized_pnl} USDT."
        ),
        payload={"position_id": str(position.id), "pnl": str(position.realized_pnl)},
    )


def notify_stop_loss_triggered(user, position) -> None:
    """T14 ✅"""
    NotificationService().send(
        user=user,
        event_type="STOP_LOSS_TRIGGERED",
        title=f"Stop Loss Hit: {position.trading_pair.symbol}",
        message=f"Stop loss triggered for {position.trading_pair.symbol}.",
        payload={"position_id": str(position.id)},
    )


def notify_take_profit_reached(user, position, level: int = 1) -> None:
    """T14 ✅"""
    NotificationService().send(
        user=user,
        event_type="TAKE_PROFIT_REACHED",
        title=f"Take Profit {level} Reached: {position.trading_pair.symbol}",
        message=f"TP{level} reached for {position.trading_pair.symbol}.",
        payload={"position_id": str(position.id), "level": level},
    )


def notify_risk_warning(user, rule: str, message: str) -> None:
    """T14 ✅"""
    NotificationService().send(
        user=user,
        event_type="RISK_WARNING",
        title="Risk Warning",
        message=message,
        payload={"rule": rule},
    )


def notify_exchange_offline(user, exchange_name: str) -> None:
    """T14 ✅"""
    NotificationService().send(
        user=user,
        event_type="EXCHANGE_OFFLINE",
        title=f"Exchange Offline: {exchange_name}",
        message=f"{exchange_name} is currently unreachable. Trading paused.",
        payload={"exchange": exchange_name},
    )
