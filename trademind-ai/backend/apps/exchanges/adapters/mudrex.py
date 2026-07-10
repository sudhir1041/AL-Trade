"""
apps/exchanges/adapters/mudrex.py
----------------------------------
T3.2 ???  Mudrex Futures Exchange Adapter
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
from typing import Callable

from .base import (Balance, BaseExchangeAdapter, Candle, ExchangeOrder,
                   ExchangePosition, MarketInfo, OrderRequest, Ticker)

logger = logging.getLogger("trademind.exchanges.mudrex")

# Rate limit: stay well under 2 req/s
MIN_REQ_INTERVAL = 0.55  # seconds between requests
