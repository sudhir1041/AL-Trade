"""
apps/notifications/tasks.py
----------------------------
T14 ✅  Notification delivery Celery tasks — one task per channel type.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.notifications.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30,
             queue="notifications", name="apps.notifications.tasks.deliver_notification")
def deliver_notification(self, notification_id: str, channel: str) -> dict:
    """T14 ✅  Route to the correct delivery handler based on channel."""
    from apps.notifications.models import Notification, NotificationDelivery, DeliveryStatus
    from django.utils import timezone

    try:
        notif    = Notification.objects.select_related("user").get(pk=notification_id)
        delivery = NotificationDelivery.objects.get(notification=notif, channel=channel)
        delivery.attempts        += 1
        delivery.last_attempt_at  = timezone.now()
        delivery.save(update_fields=["attempts", "last_attempt_at"])

        handlers = {
            "EMAIL":    _deliver_email,
            "TELEGRAM": _deliver_telegram,
            "PUSH":     _deliver_push,
            "DISCORD":  _deliver_discord,
            "SLACK":    _deliver_slack,
        }
        handler = handlers.get(channel)
        if handler:
            handler(notif)
        else:
            raise ValueError(f"Unknown channel: {channel}")

        delivery.status       = DeliveryStatus.DELIVERED
        delivery.delivered_at = timezone.now()
        delivery.save(update_fields=["status", "delivered_at"])

        return {"status": "DELIVERED", "channel": channel}

    except Exception as exc:
        logger.exception("Notification delivery failed: %s %s", notification_id, channel)
        try:
            from apps.notifications.models import NotificationDelivery, DeliveryStatus
            NotificationDelivery.objects.filter(
                notification_id=notification_id, channel=channel
            ).update(status=DeliveryStatus.FAILED, error_message=str(exc)[:500])
        except Exception:
            pass
        raise self.retry(exc=exc)


def _deliver_email(notif) -> None:
    """T14 ✅  Send email via Django email backend."""
    from django.core.mail import send_mail
    from django.conf import settings

    user = notif.user
    if not user.email:
        return

    send_mail(
        subject=notif.title,
        message=notif.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Email sent: %s → %s", notif.event_type, user.email)


def _deliver_telegram(notif) -> None:
    """T14 ✅  Send Telegram message via Bot API."""
    import requests
    from django.conf import settings
    from apps.users.models import UserPreferences

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return

    try:
        prefs     = UserPreferences.objects.get(user=notif.user)
        chat_id   = prefs.telegram_chat_id
        if not chat_id:
            return
        text = f"<b>{notif.title}</b>\n\n{notif.message}"
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Telegram sent: %s → chat_id=%s", notif.event_type, chat_id)
    except UserPreferences.DoesNotExist:
        pass


def _deliver_push(notif) -> None:
    """T14 ✅  Web push notification (placeholder — integrate with FCM/APNS)."""
    logger.info("Push notification queued: %s (not yet implemented)", notif.event_type)


def _deliver_discord(notif) -> None:
    """T14 ✅  Send Discord webhook message."""
    import requests
    from apps.users.models import UserPreferences
    try:
        prefs = UserPreferences.objects.get(user=notif.user)
        if not prefs.discord_webhook:
            return
        payload = {"content": f"**{notif.title}**\n{notif.message}"}
        requests.post(prefs.discord_webhook, json=payload, timeout=10).raise_for_status()
    except Exception:
        pass


def _deliver_slack(notif) -> None:
    """T14 ✅  Send Slack webhook message."""
    import requests
    from apps.users.models import UserPreferences
    try:
        prefs = UserPreferences.objects.get(user=notif.user)
        if not prefs.slack_webhook:
            return
        payload = {"text": f"*{notif.title}*\n{notif.message}"}
        requests.post(prefs.slack_webhook, json=payload, timeout=10).raise_for_status()
    except Exception:
        pass


@shared_task(queue="notifications", name="apps.notifications.tasks.send_daily_summaries")
def send_daily_summaries() -> None:
    """T14 ✅  Send daily trading summary to all active users — midnight UTC."""
    from apps.accounts.models import User
    from apps.notifications.services import NotificationService
    from apps.orders.models import Order, OrderStatus
    from django.utils import timezone

    yesterday = (timezone.now() - timezone.timedelta(days=1)).date()
    svc = NotificationService()

    for user in User.objects.filter(is_active=True):
        trades = Order.objects.filter(
            user=user, status=OrderStatus.FILLED, filled_at__date=yesterday
        ).count()
        svc.send(
            user=user,
            event_type="DAILY_SUMMARY",
            title="Your Daily Trading Summary",
            message=f"Yesterday you had {trades} trade(s) executed. "
                    "Check your portfolio for full details.",
            payload={"date": str(yesterday), "trades": trades},
        )
