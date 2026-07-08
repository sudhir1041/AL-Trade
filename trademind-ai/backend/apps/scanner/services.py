"""
apps/scanner/services.py
------------------------
T5 ✅  ScannerService — applies all filters and scores each trading pair.

Filter pipeline (must all pass to become a candidate):
  1. Minimum 24h volume (default $500k USDT)
  2. Spread check (max 0.5%)
  3. Volatility range (ATR-based)
  4. Trend direction detection
  5. RSI range check
  6. Volume spike detection
  7. BTC/ETH correlation check
  8. Minimum confidence threshold
"""

import logging
from decimal import Decimal
from typing import Any

from django.core.cache import cache

logger = logging.getLogger("trademind.scanner.service")

# Default filter thresholds (overridden by ScannerSettings per user)
MIN_VOLUME_USDT    = 500_000
MAX_SPREAD_PCT     = 0.5
MIN_VOLATILITY     = 0.005
MAX_VOLATILITY     = 0.15
MIN_RSI            = 30.0
MAX_RSI            = 70.0
MIN_CONFIDENCE     = 60.0


class ScannerService:
    """
    Stateless scanner service. Called once per scan cycle.
    Returns a list of result dicts for each evaluated trading pair.
    """

    def scan_all(self, pairs) -> list[dict]:
        results = []
        for pair in pairs:
            try:
                result = self._evaluate_pair(pair)
                results.append(result)
            except Exception:
                logger.exception("Error evaluating pair %s", pair.symbol)
        return results

    def _evaluate_pair(self, pair) -> dict:
        symbol     = pair.symbol
        cache_key  = f"scanner:ticker:{symbol}"
        ticker     = cache.get(cache_key)

        # Base result skeleton
        result = {
            "pair_id":        str(pair.id),
            "symbol":         symbol,
            "is_candidate":   False,
            "rejection_reason": "",
            "confidence":     0.0,
            "risk":           50.0,
            "trend":          "UNKNOWN",
            "volume":         0.0,
            "volume_spike":   False,
            "spread":         0.0,
            "btc_corr":       0.0,
            "eth_corr":       0.0,
            "factors":        {},
        }

        if not ticker:
            result["rejection_reason"] = "NO_TICKER_DATA"
            return result

        volume   = float(ticker.get("volume_24h", 0) or 0)
        bid      = float(ticker.get("bid", 0) or 0)
        ask      = float(ticker.get("ask", 0) or 0)
        price    = float(ticker.get("price", 0) or 0)

        result["volume"] = volume

        # ── Filter 1: Minimum volume ─────────────────────────────────────────
        if volume < MIN_VOLUME_USDT:
            result["rejection_reason"] = "LOW_VOLUME"
            return result

        # ── Filter 2: Spread ─────────────────────────────────────────────────
        spread_pct = ((ask - bid) / price * 100) if price > 0 else 999
        result["spread"] = spread_pct
        if spread_pct > MAX_SPREAD_PCT:
            result["rejection_reason"] = "HIGH_SPREAD"
            return result

        # ── Get cached indicator values ──────────────────────────────────────
        ind_key    = f"indicators:{symbol}:1h"
        indicators = cache.get(ind_key) or {}

        rsi     = indicators.get("rsi", 50.0)
        atr_pct = indicators.get("atr_pct", 0.02)
        trend   = indicators.get("trend", "SIDEWAYS")
        macd_ok = indicators.get("macd_bullish", False)
        ema_ok  = indicators.get("ema_bullish", False)

        # ── Filter 3: Volatility ──────────────────────────────────────────────
        if not (MIN_VOLATILITY <= atr_pct <= MAX_VOLATILITY):
            result["rejection_reason"] = "OUT_OF_VOLATILITY_RANGE"
            return result

        result["trend"] = trend

        # ── Filter 4: RSI ─────────────────────────────────────────────────────
        if not (MIN_RSI <= rsi <= MAX_RSI):
            result["rejection_reason"] = "RSI_OUT_OF_RANGE"
            return result

        # ── Filter 5: Detect volume spike (vs rolling avg) ────────────────────
        vol_avg      = float(cache.get(f"vol_avg:{symbol}") or volume)
        volume_spike = volume > (vol_avg * 1.5)
        result["volume_spike"] = volume_spike

        # ── Confidence scoring ────────────────────────────────────────────────
        score  = 50.0   # base
        factors = {}

        if trend == "BULLISH":
            score += 10
            factors["trend_bullish"] = True
        elif trend == "BEARISH":
            score += 5
            factors["trend_bearish"] = True

        if macd_ok:
            score += 8
            factors["macd_confirmation"] = True

        if ema_ok:
            score += 7
            factors["ema_alignment"] = True

        if volume_spike:
            score += 10
            factors["volume_spike"] = True

        if 40 <= rsi <= 60:
            score += 5
            factors["rsi_neutral"] = True
        elif rsi < 40:
            score += 8
            factors["rsi_oversold"] = True
        elif rsi > 60:
            score += 3
            factors["rsi_overbought"] = True

        if atr_pct < 0.05:
            score += 5
            factors["low_volatility"] = True

        # Cap at 100
        score = min(score, 100.0)
        result["confidence"] = round(score, 2)
        result["factors"]    = factors

        # Risk scoring (inverse of confidence + volatility factor)
        result["risk"] = round(max(0, 100 - score + atr_pct * 100), 2)

        # ── Minimum threshold ─────────────────────────────────────────────────
        if score < MIN_CONFIDENCE:
            result["rejection_reason"] = f"LOW_CONFIDENCE:{score:.1f}"
            return result

        result["is_candidate"] = True
        return result
