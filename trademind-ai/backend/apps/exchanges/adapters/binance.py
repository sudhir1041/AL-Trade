import logging
from decimal import Decimal

from .base import BaseExchangeAdapter, ExchangeOrder, Ticker

logger = logging.getLogger("trademind.exchanges.binance")


class BinanceAdapter(BaseExchangeAdapter):
    exchange_slug = "binance"
    exchange_name = "Binance"

    async def connect(self):
        self._connected = True
        return True

    async def disconnect(self):
        self._connected = False

    async def ping(self):
        return True

    async def get_markets(self):
        return []

    async def get_ticker(self, symbol):
        return None

    async def get_candles(self, symbol, timeframe, limit=200):
        return []

    async def get_balance(self, currency="USDT"):
        return []

    async def get_positions(self, currency="USDT"):
        return []

    async def get_open_orders(self, symbol=None, currency="USDT"):
        return []

    async def get_order_history(self, symbol=None, limit=50, currency="USDT"):
        return []

    async def place_order(self, req):
        return None

    async def cancel_order(self, order_id, symbol):
        return True

    async def close_position(self, position_id, quantity=None):
        return True

    async def set_stop_loss_take_profit(
        self, position_id, stop_loss_price=None, take_profit_price=None
    ):
        return True

    async def set_leverage(self, symbol, leverage, margin_type="ISOLATED"):
        return True

    async def subscribe_ticker(self, symbols, callback):
        pass

    async def subscribe_kline(self, symbol, timeframe, callback):
        pass

    async def unsubscribe_all(self):
        pass
