"""
apps/exchanges/adapters/mudrex.py
----------------------------------
T3.2 ✅ Mudrex Futures Exchange Adapter
Uses the official mudrex-sdk (pip install mudrex-sdk).

SDK docs: https://docs.trade.mudrex.com/docs/python-sdk
GitHub:   https://github.com/mudrex/mudrex-python-sdk

Key SDK facts:
  - TradeClient(api_secret="...")  or env MUDREX_API_SECRET
  - Rate limits: 2 req/s | 50/min | 1000/hr | 10000/day
  - Order side: LONG | SHORT  (not BUY/SELL)
  - trigger_type: MARKET | LIMIT
  - List responses: use .id  |  Single object: use .order_id
  - All numeric values passed as strings for precision
  - Only USDT trade_currency supported
"""

import asyncio
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Any

import requests
import websockets
from mudrex import TradeClient, MudrexAPIError, MudrexRequestError

from .base import (
    Balance, BaseExchangeAdapter, Candle, ExchangeOrder,
    ExchangePosition, MarketInfo, OrderRequest, Ticker,
)

logger = logging.getLogger("trademind.exchanges.mudrex")

# Rate limit: stay well under 2 req/s
MIN_REQ_INTERVAL = 0.55   # seconds between requests

class MudrexAdapter(BaseExchangeAdapter):
    exchange_slug: str = "mudrex"
    exchange_name: str = "Mudrex"
    supports_futures: bool = True
    supports_spot: bool = False

    def __init__(self, api_secret: str, is_testnet: bool = False):
        super().__init__(api_secret, is_testnet)
        self.client = None
        self._last_req_time = 0.0
        self._req_lock = asyncio.Lock()

        # WebSocket state
        self._ws_tasks = []
        self._ws_callbacks = {}

    async def _rate_limit(self):
        """Enforce rate limits"""
        async with self._req_lock:
            now = time.time()
            elapsed = now - self._last_req_time
            if elapsed < MIN_REQ_INTERVAL:
                await asyncio.sleep(MIN_REQ_INTERVAL - elapsed)
            self._last_req_time = time.time()

    async def connect(self) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await self._rate_limit()
            # client connection does automatic ping/auth under the hood
            def _connect():
                return TradeClient(api_secret=self.api_secret)
            self.client = await loop.run_in_executor(None, _connect)
            self._connected = True
            return True
        except (MudrexAPIError, MudrexRequestError, Exception) as e:
            logger.error(f"Failed to connect to Mudrex: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        await self.unsubscribe_all()
        self._connected = False
        self.client = None

    async def ping(self) -> bool:
        if not self._connected or not self.client:
            return False
        try:
            loop = asyncio.get_event_loop()
            await self._rate_limit()
            await loop.run_in_executor(None, self.client.get_wallet_funds)
            return True
        except Exception:
            return False

    async def get_markets(self) -> list[MarketInfo]:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            resp = await loop.run_in_executor(None, lambda: self.client.list_futures(limit=100))

            markets = []
            for item in resp:
                symbol = item.get("symbol")
                if not symbol:
                    continue
                markets.append(
                    MarketInfo(
                        symbol=symbol,
                        base_asset=item.get("base_asset", symbol.replace("USDT", "")),
                        quote_asset=item.get("quote_asset", "USDT"),
                        is_active=item.get("status", "ACTIVE") == "ACTIVE",
                        is_futures=True,
                        min_quantity=self._to_decimal(item.get("min_quantity", "0.001")),
                        max_quantity=self._to_decimal(item.get("max_quantity", "1000000")),
                        quantity_step=self._to_decimal(item.get("quantity_step", "0.001")),
                        price_step=self._to_decimal(item.get("price_step", "0.01")),
                        min_notional=self._to_decimal(item.get("min_notional", "5.0")),
                        raw=item,
                    )
                )
            return markets
        except Exception as e:
            logger.error(f"Error getting markets: {e}")
            raise

    async def get_ticker(self, symbol: str) -> Ticker:
        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            def fetch():
                r = requests.get(f"https://trade.mudrex.com/fapi/v1/price/ticker/24hr?symbol={symbol}")
                r.raise_for_status()
                return r.json()

            resp = await loop.run_in_executor(None, fetch)
            data = resp[0] if isinstance(resp, list) and len(resp) > 0 else resp

            return Ticker(
                symbol=symbol,
                price=self._to_decimal(data.get("last_price")),
                bid=self._to_decimal(data.get("best_bid_price", data.get("last_price"))),
                ask=self._to_decimal(data.get("best_ask_price", data.get("last_price"))),
                high_24h=self._to_decimal(data.get("high_price")),
                low_24h=self._to_decimal(data.get("low_price")),
                volume_24h=self._to_decimal(data.get("volume")),
                change_24h_pct=self._to_decimal(data.get("price_change_percent")),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            raise

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            def fetch():
                r = requests.get(
                    f"https://trade.mudrex.com/fapi/v1/price/klines?symbol={symbol}&interval={timeframe}&limit={limit}"
                )
                r.raise_for_status()
                return r.json()

            resp = await loop.run_in_executor(None, fetch)

            candles = []
            for item in resp:
                if len(item) >= 6:
                    candles.append(
                        Candle(
                            symbol=symbol,
                            timeframe=timeframe,
                            open=self._to_decimal(item[1]),
                            high=self._to_decimal(item[2]),
                            low=self._to_decimal(item[3]),
                            close=self._to_decimal(item[4]),
                            volume=self._to_decimal(item[5]),
                            timestamp=datetime.fromtimestamp(int(item[0]) / 1000.0, tz=timezone.utc).replace(tzinfo=None)
                        )
                    )
            return candles
        except Exception as e:
            logger.error(f"Error getting candles for {symbol}: {e}")
            raise

    async def get_balance(self, currency: str = "USDT") -> list[Balance]:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            def fetch():
                return self.client._get("/futures/wallet", params={"trade_currency": currency})

            try:
                resp = await loop.run_in_executor(None, fetch)
            except AttributeError:
                resp = await loop.run_in_executor(None, self.client.get_wallet_funds)

            balances = []

            if isinstance(resp, dict):
                balances.append(
                    Balance(
                        asset=currency,
                        available=self._to_decimal(resp.get("available_balance", "0")),
                        locked=self._to_decimal(resp.get("locked_balance", "0")),
                        total=self._to_decimal(resp.get("total_balance", "0"))
                    )
                )
            elif isinstance(resp, list):
                for item in resp:
                    asset = item.get("asset", currency)
                    if asset == currency:
                        balances.append(
                            Balance(
                                asset=asset,
                                available=self._to_decimal(item.get("available_balance", "0")),
                                locked=self._to_decimal(item.get("locked_balance", "0")),
                                total=self._to_decimal(item.get("total_balance", "0"))
                            )
                        )

            if not balances:
                balances.append(Balance(asset=currency, available=Decimal("0"), locked=Decimal("0"), total=Decimal("0")))

            return balances
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise

    async def get_positions(self, currency: str = "USDT") -> list[ExchangePosition]:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            self.client._trade_currency = currency
            resp = await loop.run_in_executor(None, lambda: self.client.get_positions(limit=100))

            positions = []
            for item in resp:
                qty = self._to_decimal(item.get("quantity", "0"))
                if qty == 0:
                    continue

                positions.append(
                    ExchangePosition(
                        symbol=item.get("symbol", "UNKNOWN"),
                        side=item.get("position_side", item.get("order_type", "LONG")),
                        entry_price=self._to_decimal(item.get("entry_price", "0")),
                        quantity=qty,
                        unrealized_pnl=self._to_decimal(item.get("unrealized_pnl", "0")),
                        margin=self._to_decimal(item.get("margin", "0")),
                        leverage=int(item.get("leverage", 1)),
                        liquidation_price=self._to_decimal(item.get("liquidation_price", "0")),
                        stop_loss_price=self._to_decimal(item.get("stoploss_price")) if item.get("stoploss_price") else None,
                        take_profit_price=self._to_decimal(item.get("takeprofit_price")) if item.get("takeprofit_price") else None,
                        position_id=item.get("id"),
                        trade_currency=currency,
                        raw=item
                    )
                )
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise

    async def get_open_orders(self, symbol: str | None = None, currency: str = "USDT") -> list[ExchangeOrder]:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            self.client._trade_currency = currency
            resp = await loop.run_in_executor(None, lambda: self.client.get_orders(limit=100))

            orders = []
            for item in resp:
                order_symbol = item.get("symbol")
                if symbol and order_symbol != symbol:
                    continue

                status = item.get("status", "OPEN")

                orders.append(
                    ExchangeOrder(
                        order_id=item.get("id"),
                        client_order_id=item.get("client_order_id", ""),
                        symbol=order_symbol,
                        side=item.get("order_type", "LONG"),
                        order_type=item.get("trigger_type", "MARKET"),
                        status=status,
                        quantity=self._to_decimal(item.get("quantity", "0")),
                        price=self._to_decimal(item.get("order_price", "0")),
                        filled_quantity=self._to_decimal(item.get("filled_quantity", "0")),
                        avg_fill_price=self._to_decimal(item.get("average_fill_price", "0")),
                        commission=self._to_decimal(item.get("commission", "0")),
                        commission_asset=item.get("commission_asset", currency),
                        created_at=datetime.utcnow(),
                        raw=item
                    )
                )
            return orders
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            raise

    async def get_order_history(self, symbol: str | None = None, limit: int = 50, currency: str = "USDT") -> list[ExchangeOrder]:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            self.client._trade_currency = currency
            resp = await loop.run_in_executor(None, lambda: self.client.get_order_history(limit=limit))

            orders = []
            for item in resp:
                order_symbol = item.get("symbol")
                if symbol and order_symbol != symbol:
                    continue

                orders.append(
                    ExchangeOrder(
                        order_id=item.get("id"),
                        client_order_id=item.get("client_order_id", ""),
                        symbol=order_symbol,
                        side=item.get("order_type", "LONG"),
                        order_type=item.get("trigger_type", "MARKET"),
                        status=item.get("status", "FILLED"),
                        quantity=self._to_decimal(item.get("quantity", "0")),
                        price=self._to_decimal(item.get("order_price", "0")),
                        filled_quantity=self._to_decimal(item.get("filled_quantity", "0")),
                        avg_fill_price=self._to_decimal(item.get("average_fill_price", "0")),
                        commission=self._to_decimal(item.get("commission", "0")),
                        commission_asset=item.get("commission_asset", currency),
                        created_at=datetime.utcnow(),
                        raw=item
                    )
                )
            return orders
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            raise

    async def place_order(self, req: OrderRequest) -> ExchangeOrder:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            self.client._trade_currency = req.trade_currency

            is_sl = req.stop_loss_price is not None
            is_tp = req.take_profit_price is not None

            def execute():
                return self.client.place_order(
                    symbol=req.symbol,
                    leverage=str(req.leverage),
                    quantity=str(req.quantity),
                    order_type=req.side,  # "LONG" or "SHORT"
                    trigger_type=req.order_type, # "MARKET" or "LIMIT"
                    order_price=str(req.price) if req.price else None,
                    is_stoploss=is_sl,
                    is_takeprofit=is_tp,
                    stoploss_price=str(req.stop_loss_price) if is_sl else None,
                    takeprofit_price=str(req.take_profit_price) if is_tp else None,
                    reduce_only=req.reduce_only
                )

            resp = await loop.run_in_executor(None, execute)

            return ExchangeOrder(
                order_id=getattr(resp, "order_id", getattr(resp, "id", "")),
                client_order_id=req.client_order_id or "",
                symbol=req.symbol,
                side=req.side,
                order_type=req.order_type,
                status="OPEN" if req.order_type == "LIMIT" else "FILLED",
                quantity=req.quantity,
                price=req.price or Decimal("0"),
                raw={"order_id": getattr(resp, "order_id", getattr(resp, "id", ""))}
            )
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            await loop.run_in_executor(None, lambda: self.client.cancel_order(order_id))
            return True
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False

    async def close_position(self, position_id: str, quantity: Decimal | None = None) -> bool:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            if quantity is not None:
                raise Exception("Partial close requires side, which is not implemented in this generic method")
            else:
                await loop.run_in_executor(None, lambda: self.client.close_position(position_id))
            return True
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return False

    async def set_stop_loss_take_profit(self, position_id: str, stop_loss_price: Decimal | None = None, take_profit_price: Decimal | None = None) -> bool:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            is_sl = stop_loss_price is not None
            is_tp = take_profit_price is not None

            if not is_sl and not is_tp:
                return False

            def execute():
                return self.client.place_risk_order(
                    position_id=position_id,
                    is_stoploss=is_sl,
                    is_takeprofit=is_tp,
                    stoploss_price=str(stop_loss_price) if is_sl else None,
                    takeprofit_price=str(take_profit_price) if is_tp else None
                )

            await loop.run_in_executor(None, execute)
            return True
        except Exception as e:
            logger.error(f"Error setting SL/TP (might need amend instead): {e}")
            try:
                is_sl = stop_loss_price is not None
                is_tp = take_profit_price is not None

                def execute_amend():
                    return self.client.amend_risk_order(
                        position_id=position_id,
                        is_stoploss=is_sl,
                        is_takeprofit=is_tp,
                        stoploss_price=str(stop_loss_price) if is_sl else None,
                        takeprofit_price=str(take_profit_price) if is_tp else None
                    )
                await loop.run_in_executor(None, execute_amend)
                return True
            except Exception as e2:
                logger.error(f"Error amending SL/TP: {e2}")
                return False

    async def set_leverage(self, symbol: str, leverage: int, margin_type: str = "ISOLATED") -> bool:
        if not self.client:
            raise Exception("Mudrex client not initialized")

        loop = asyncio.get_event_loop()
        await self._rate_limit()

        try:
            def execute():
                return self.client.set_leverage(symbol, leverage=leverage)

            await loop.run_in_executor(None, execute)
            return True
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return False

    async def _ws_connect_and_listen(self, url: str, symbols: list[str], callback, channel: str):
        try:
            async with websockets.connect(url) as ws:
                params = []
                for sym in symbols:
                    sym_lower = sym.lower().replace("usdt", "_usdt")
                    params.append(f"{sym_lower}@{channel}")

                sub_msg = {
                    "method": "SUBSCRIBE",
                    "params": params,
                    "id": int(time.time() * 1000)
                }
                await ws.send(json.dumps(sub_msg))

                while self._connected:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if callback:
                        await callback(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def subscribe_ticker(self, symbols: list[str], callback) -> None:
        url = "wss://stream.trade.mudrex.com/fapi/ws"
        task = asyncio.create_task(self._ws_connect_and_listen(url, symbols, callback, "ticker"))
        self._ws_tasks.append(task)

    async def subscribe_kline(self, symbol: str, timeframe: str, callback) -> None:
        url = "wss://stream.trade.mudrex.com/fapi/ws"
        channel = f"kline_{timeframe}"
        task = asyncio.create_task(self._ws_connect_and_listen(url, [symbol], callback, channel))
        self._ws_tasks.append(task)

    async def unsubscribe_all(self) -> None:
        for task in self._ws_tasks:
            task.cancel()
        self._ws_tasks.clear()
