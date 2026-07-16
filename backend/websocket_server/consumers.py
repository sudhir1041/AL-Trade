"""
websocket_server/consumers.py
------------------------------
T4.2 ✅  Django Channels WebSocket consumers.

Channels:
  Public:  market.ticker, market.ohlcv, market.orderbook
  Private: portfolio.balance, portfolio.positions,
           orders.status, notifications, scanner.results,
           ai.recommendations

Every private channel requires a valid JWT token passed as a
query param: ?token=<access_token>
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebSocketConsumer
from django.core.cache import cache

logger = logging.getLogger("trademind.websocket")


# ─────────────────────────────────────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────────────────────────────────────

async def _authenticate(scope) -> tuple:
    """Extract JWT from query string and return (user, error_msg)."""
    from urllib.parse import parse_qs
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from apps.accounts.models import User

    qs    = parse_qs(scope.get("query_string", b"").decode())
    token = qs.get("token", [None])[0]
    if not token:
        return None, "No token provided."
    try:
        payload = AccessToken(token)
        user_id = payload["user_id"]
        user    = await database_sync_to_async(User.objects.get)(pk=user_id)
        return user, None
    except (TokenError, User.DoesNotExist, Exception) as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Public: Market Ticker
# ─────────────────────────────────────────────────────────────────────────────

class MarketTickerConsumer(AsyncWebSocketConsumer):
    """
    T4.2 ✅  ws://host/ws/market/ticker/{symbol}/
    Streams live ticker updates for a single symbol.
    Client receives updates whenever the ticker cache is refreshed.
    """

    async def connect(self):
        self.symbol   = self.scope["url_route"]["kwargs"].get("symbol", "BTCUSDT").upper()
        self.group    = f"ticker_{self.symbol}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.debug("WS connected: ticker %s", self.symbol)

        # Send current cached ticker immediately on connect
        ticker = cache.get(f"ticker:{self.symbol}")
        if ticker:
            await self.send(text_data=json.dumps({
                "event":   "market.ticker",
                "symbol":  self.symbol,
                "payload": ticker,
            }))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def ticker_update(self, event):
        """Called by channel layer when ticker is refreshed."""
        await self.send(text_data=json.dumps({
            "event":   "market.ticker",
            "symbol":  self.symbol,
            "payload": event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Public: OHLCV Candles
# ─────────────────────────────────────────────────────────────────────────────

class MarketOHLCVConsumer(AsyncWebSocketConsumer):
    """
    T4.2 ✅  ws://host/ws/market/ohlcv/{symbol}/{timeframe}/
    """

    async def connect(self):
        kwargs        = self.scope["url_route"]["kwargs"]
        self.symbol   = kwargs.get("symbol", "BTCUSDT").upper()
        self.timeframe = kwargs.get("timeframe", "1m")
        self.group    = f"ohlcv_{self.symbol}_{self.timeframe}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def candle_update(self, event):
        await self.send(text_data=json.dumps({
            "event":     "market.ohlcv",
            "symbol":    self.symbol,
            "timeframe": self.timeframe,
            "payload":   event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Private base — handles JWT auth
# ─────────────────────────────────────────────────────────────────────────────

class PrivateConsumerBase(AsyncWebSocketConsumer):
    """Base class for all authenticated WebSocket consumers."""

    async def connect(self):
        user, error = await _authenticate(self.scope)
        if error:
            await self.close(code=4001)
            return
        self.user = user
        await self._on_authenticated()

    async def _on_authenticated(self):
        """Override in subclass to join groups and accept."""
        raise NotImplementedError

    async def receive(self, text_data=None, bytes_data=None):
        """Handle ping/pong and subscription messages."""
        if not text_data:
            return
        try:
            msg = json.loads(text_data)
            if msg.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Private: Portfolio updates
# ─────────────────────────────────────────────────────────────────────────────

class PortfolioConsumer(PrivateConsumerBase):
    """
    T4.2 ✅  ws://host/ws/portfolio/?token=<jwt>
    Streams portfolio balance + position updates.
    """

    async def _on_authenticated(self):
        self.group = f"portfolio_{self.user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        logger.debug("WS connected: portfolio user=%s", self.user.id)

        # Send initial snapshot
        snapshot = await self._get_portfolio_snapshot()
        await self.send(text_data=json.dumps({
            "event":   "portfolio.snapshot",
            "payload": snapshot,
        }))

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    @database_sync_to_async
    def _get_portfolio_snapshot(self) -> dict:
        from apps.portfolio.models import Portfolio
        portfolios = Portfolio.objects.filter(user=self.user).values(
            "total_balance", "available_balance", "unrealized_pnl", "realized_pnl"
        )
        return {
            "portfolios": [
                {k: str(v) if hasattr(v, "__round__") else v for k, v in p.items()}
                for p in portfolios
            ]
        }

    async def portfolio_update(self, event):
        await self.send(text_data=json.dumps({
            "event":   "portfolio.balance",
            "payload": event["payload"],
        }))

    async def position_update(self, event):
        await self.send(text_data=json.dumps({
            "event":   "portfolio.positions",
            "payload": event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Private: Order updates
# ─────────────────────────────────────────────────────────────────────────────

class OrderConsumer(PrivateConsumerBase):
    """
    T4.2 ✅  ws://host/ws/orders/?token=<jwt>
    Streams order status changes and execution confirmations.
    """

    async def _on_authenticated(self):
        self.group = f"orders_{self.user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def order_update(self, event):
        await self.send(text_data=json.dumps({
            "event":   "orders.status",
            "payload": event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Private: Notifications
# ─────────────────────────────────────────────────────────────────────────────

class NotificationConsumer(PrivateConsumerBase):
    """
    T4.2 ✅  ws://host/ws/notifications/?token=<jwt>
    Pushes real-time notifications to the user's browser.
    """

    async def _on_authenticated(self):
        self.group = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notification_push(self, event):
        await self.send(text_data=json.dumps({
            "event":   "notification",
            "payload": event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Private: Scanner results
# ─────────────────────────────────────────────────────────────────────────────

class ScannerConsumer(PrivateConsumerBase):
    """
    T4.2 ✅  ws://host/ws/scanner/?token=<jwt>
    Pushes scanner results and AI candidates in real-time.
    """

    async def _on_authenticated(self):
        self.group = "scanner_results"   # broadcast to all connected users
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def scanner_update(self, event):
        await self.send(text_data=json.dumps({
            "event":   "scanner.results",
            "payload": event["payload"],
        }))


# ─────────────────────────────────────────────────────────────────────────────
# Private: AI Recommendations
# ─────────────────────────────────────────────────────────────────────────────

class AIRecommendationConsumer(PrivateConsumerBase):
    """
    T4.2 ✅  ws://host/ws/ai/?token=<jwt>
    Pushes AI score updates and trading recommendations.
    """

    async def _on_authenticated(self):
        self.group = f"ai_{self.user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def ai_recommendation(self, event):
        await self.send(text_data=json.dumps({
            "event":   "ai.recommendations",
            "payload": event["payload"],
        }))
