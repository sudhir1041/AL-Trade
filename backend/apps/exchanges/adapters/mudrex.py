"""
apps/exchanges/adapters/mudrex.py
----------------------------------
Mudrex Futures Exchange Adapter
Using raw requests with requests library
"""

import logging
from decimal import Decimal
from typing import Any
import httpx

from .base import (
    Balance, BaseExchangeAdapter, Candle, ExchangeOrder,
    ExchangePosition, MarketInfo, OrderRequest, Ticker,
)

logger = logging.getLogger("trademind.exchanges.mudrex")

class MudrexAdapter(BaseExchangeAdapter):
    exchange_slug: str = "mudrex"
    exchange_name: str = "Mudrex"
    supports_futures: bool = True
    supports_spot: bool = False

    def __init__(self, api_secret: str, is_testnet: bool = False):
        super().__init__(api_secret, is_testnet)
        self.base_url = "https://trade.mudrex.com/fapi/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-Authentication": self.api_secret}
        )

    async def connect(self) -> bool:
        try:
            res = await self.client.get("/users/balances")
            self._connected = res.status_code == 200
            return self._connected
        except Exception as e:
            logger.error(f"Failed to connect Mudrex: {e}")
            return False

    async def disconnect(self) -> None:
        await self.client.aclose()
        self._connected = False

    async def ping(self) -> bool:
        return await self.connect()

    async def get_markets(self) -> list[MarketInfo]:
        res = await self.client.get("/markets")
        if res.status_code != 200:
            return []

        markets = []
        for m in res.json().get('data', []):
            markets.append(MarketInfo(
                symbol=m.get('symbol'),
                base_asset=m.get('baseAsset', ''),
                quote_asset=m.get('quoteAsset', 'USDT'),
                raw=m
            ))
        return markets

    async def get_ticker(self, symbol: str) -> Ticker:
        res = await self.client.get(f"/ticker?symbol={symbol}")
        data = res.json()
        return Ticker(
            symbol=symbol,
            price=self._to_decimal(data.get("lastPrice", "0")),
            raw=data
        )

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        return []

    async def get_balance(self, currency: str = "USDT") -> list[Balance]:
        res = await self.client.get("/users/balances")
        balances = []
        for b in res.json().get('data', []):
            balances.append(Balance(
                asset=b.get('asset', 'USDT'),
                available=self._to_decimal(b.get('availableBalance', '0')),
                locked=self._to_decimal(b.get('lockedBalance', '0')),
                total=self._to_decimal(b.get('totalBalance', '0'))
            ))
        return balances

    async def get_positions(self, currency: str = "USDT") -> list[ExchangePosition]:
        res = await self.client.get("/users/positions")
        positions = []
        for p in res.json().get('data', []):
            positions.append(ExchangePosition(
                symbol=p.get('symbol', ''),
                side=p.get('positionSide', 'LONG'),
                entry_price=self._to_decimal(p.get('entryPrice', '0')),
                quantity=self._to_decimal(p.get('positionAmount', '0')),
                unrealized_pnl=self._to_decimal(p.get('unRealizedProfit', '0')),
                margin=self._to_decimal(p.get('isolatedMargin', '0')),
                leverage=int(p.get('leverage', 1)),
                raw=p
            ))
        return positions

    async def get_open_orders(self, symbol: str | None = None, currency: str = "USDT") -> list[ExchangeOrder]:
        return []

    async def get_order_history(self, symbol: str | None = None, limit: int = 50, currency: str = "USDT") -> list[ExchangeOrder]:
        return []

    async def place_order(self, req: OrderRequest) -> ExchangeOrder:
        payload = {
            "symbol": req.symbol,
            "side": "BUY" if req.side == "LONG" else "SELL",
            "type": req.order_type,
            "quantity": str(req.quantity),
        }
        if req.price:
            payload["price"] = str(req.price)

        res = await self.client.post("/orders", json=payload)
        data = res.json().get('data', {})
        return ExchangeOrder(
            order_id=str(data.get("orderId", "")),
            client_order_id=str(data.get("clientOrderId", "")),
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            status=data.get("status", "NEW"),
            quantity=req.quantity,
            price=req.price or Decimal("0"),
            raw=data
        )

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        res = await self.client.delete(f"/orders?symbol={symbol}&orderId={order_id}")
        return res.status_code == 200

    async def close_position(self, position_id: str, quantity: Decimal | None = None) -> bool:
        return False

    async def set_stop_loss_take_profit(self, position_id: str, stop_loss_price: Decimal | None = None, take_profit_price: Decimal | None = None) -> bool:
        return False
