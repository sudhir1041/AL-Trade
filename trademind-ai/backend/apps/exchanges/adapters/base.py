"""
apps/exchanges/adapters/base.py
--------------------------------
T3.1 ✅  Abstract Exchange Adapter Interface.

Every exchange adapter MUST implement this interface.
The trading engine NEVER calls exchange APIs directly —
all communication goes through adapters.

Key design rules:
- One interface, many exchanges
- Exchange-specific complexity stays inside adapters
- All adapters follow identical contracts
- Every exchange action is auditable
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Unified Data Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class MarketInfo:
    symbol: str
    base_asset: str
    quote_asset: str
    is_active: bool = True
    is_futures: bool = True
    min_quantity: Decimal = Decimal("0.001")
    max_quantity: Decimal = Decimal("1000000")
    quantity_step: Decimal = Decimal("0.001")
    price_step: Decimal = Decimal("0.01")
    min_notional: Decimal = Decimal("1.0")
    raw: dict = field(default_factory=dict)


@dataclass
class Ticker:
    symbol: str
    price: Decimal
    bid: Decimal = Decimal("0")
    ask: Decimal = Decimal("0")
    high_24h: Decimal = Decimal("0")
    low_24h: Decimal = Decimal("0")
    volume_24h: Decimal = Decimal("0")
    change_24h_pct: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Candle:
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp: datetime


@dataclass
class Balance:
    asset: str
    available: Decimal
    locked: Decimal
    total: Decimal


@dataclass
class ExchangePosition:
    symbol: str
    side: str  # "LONG" | "SHORT"
    entry_price: Decimal
    quantity: Decimal
    unrealized_pnl: Decimal
    margin: Decimal
    leverage: int
    liquidation_price: Decimal = Decimal("0")
    stop_loss_price: Decimal | None = None
    take_profit_price: Decimal | None = None
    position_id: str | None = None
    trade_currency: str = "USDT"
    raw: dict = field(default_factory=dict)


@dataclass
class ExchangeOrder:
    order_id: str
    client_order_id: str
    symbol: str
    side: str  # "LONG" | "SHORT"
    order_type: str  # "MARKET" | "LIMIT"
    status: str  # "OPEN" | "FILLED" | "CANCELLED" | "PARTIALLY_FILLED"
    quantity: Decimal
    price: Decimal
    filled_quantity: Decimal = Decimal("0")
    avg_fill_price: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    commission_asset: str = "USDT"
    created_at: datetime = field(default_factory=datetime.utcnow)
    raw: dict = field(default_factory=dict)


@dataclass
class OrderRequest:
    """Unified order request passed to adapter.place_order()"""

    symbol: str
    side: str  # "LONG" | "SHORT"
    order_type: str  # "MARKET" | "LIMIT"
    quantity: Decimal
    price: Decimal | None = None
    stop_loss_price: Decimal | None = None
    take_profit_price: Decimal | None = None
    leverage: int = 1
    reduce_only: bool = False
    trade_currency: str = "USDT"
    client_order_id: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Base Adapter Interface
# ─────────────────────────────────────────────────────────────────────────────


class BaseExchangeAdapter(ABC):
    """
    Abstract base class every exchange adapter must implement.

    Usage:
        adapter = MudrexAdapter(api_secret="your-secret")
        await adapter.connect()
        balance = await adapter.get_balance()
        order   = await adapter.place_order(OrderRequest(...))
    """

    exchange_slug: str = "base"
    exchange_name: str = "Base Exchange"
    supports_futures: bool = True
    supports_spot: bool = True

    def __init__(self, api_secret: str, is_testnet: bool = False):
        self.api_secret = api_secret
        self.is_testnet = is_testnet
        self._connected = False

    # ── Connection ──────────────────────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection and validate credentials. Returns True on success."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close all connections cleanly."""

    @abstractmethod
    async def ping(self) -> bool:
        """Health check — returns True if exchange is reachable and authenticated."""

    # ── Market Data ─────────────────────────────────────────────────────────

    @abstractmethod
    async def get_markets(self) -> list[MarketInfo]:
        """Return all active trading pairs."""

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """Return current ticker for symbol."""

    @abstractmethod
    async def get_candles(
        self, symbol: str, timeframe: str, limit: int = 200
    ) -> list[Candle]:
        """Return historical OHLCV candles."""

    # ── Account ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_balance(self, currency: str = "USDT") -> list[Balance]:
        """Return wallet balances."""

    @abstractmethod
    async def get_positions(self, currency: str = "USDT") -> list[ExchangePosition]:
        """Return all open positions."""

    @abstractmethod
    async def get_open_orders(
        self, symbol: str | None = None, currency: str = "USDT"
    ) -> list[ExchangeOrder]:
        """Return all open/pending orders."""

    @abstractmethod
    async def get_order_history(
        self, symbol: str | None = None, limit: int = 50, currency: str = "USDT"
    ) -> list[ExchangeOrder]:
        """Return historical orders."""

    # ── Trading ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def place_order(self, req: OrderRequest) -> ExchangeOrder:
        """
        Place a new order.
        MUST be called only after Risk Engine approval.
        """

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order. Returns True on success."""

    @abstractmethod
    async def close_position(
        self, position_id: str, quantity: Decimal | None = None
    ) -> bool:
        """Close a position fully or partially."""

    @abstractmethod
    async def set_stop_loss_take_profit(
        self,
        position_id: str,
        stop_loss_price: Decimal | None = None,
        take_profit_price: Decimal | None = None,
    ) -> bool:
        """Set or update SL/TP on an open position."""

    # ── Leverage ─────────────────────────────────────────────────────────────

    async def set_leverage(
        self, symbol: str, leverage: int, margin_type: str = "ISOLATED"
    ) -> bool:
        """Set leverage for a symbol. Override in adapter if supported."""
        return True

    # ── WebSocket ────────────────────────────────────────────────────────────

    async def subscribe_ticker(self, symbols: list[str], callback) -> None:
        """Subscribe to live ticker updates for symbols."""

    async def subscribe_kline(self, symbol: str, timeframe: str, callback) -> None:
        """Subscribe to live candle updates."""

    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all WebSocket streams."""

    # ── Helpers ──────────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _to_decimal(self, value: Any) -> Decimal:
        """Safely convert value to Decimal."""
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal("0")

    def _normalize_symbol(self, symbol: str) -> str:
        """Convert any symbol format to exchange-native format."""
        return symbol

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} connected={self._connected}>"
