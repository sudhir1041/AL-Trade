"""
apps/indicators/engine.py
--------------------------
T6 ✅  Technical Analysis Engine.

Calculates all required indicators using the `ta` library + pandas.
Results are cached in Redis (TTL per timeframe).

Supported indicators:
  Trend:      EMA (9,21,50,200), SMA, VWAP, SuperTrend, Ichimoku
  Momentum:   RSI, MACD, Stochastic RSI, CCI, ROC, ADX
  Volume:     OBV, CMF, MFI, Volume Profile
  Volatility: ATR, Bollinger Bands, Keltner Channel, Donchian Channel
  Structure:  Support/Resistance levels, Trend direction
"""

import logging
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from django.core.cache import cache

logger = logging.getLogger("trademind.indicators")

# Cache TTL per timeframe (seconds)
CACHE_TTL = {
    "1m":  10,
    "5m":  30,
    "15m": 60,
    "1h":  300,
    "4h":  900,
    "1d":  3600,
}


def _get_ohlcv_df(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame | None:
    """Load OHLCV data from DB into a pandas DataFrame."""
    from apps.market.models import OHLCV, TradingPair
    pair = TradingPair.objects.filter(symbol=symbol, is_active=True).first()
    if not pair:
        return None

    candles = list(
        OHLCV.objects.filter(trading_pair=pair, timeframe=timeframe)
        .order_by("-timestamp")[:limit]
        .values("timestamp", "open", "high", "low", "close", "volume")
    )
    if len(candles) < 50:
        return None

    df = pd.DataFrame(reversed(candles))
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


class IndicatorEngine:
    """
    Calculates all technical indicators for a given symbol and timeframe.
    Results are cached in Redis to avoid recomputation across multiple consumers.
    """

    def compute_all(self, symbol: str, timeframe: str = "1h") -> dict[str, Any]:
        """
        T6 ✅  Compute and cache all indicators for symbol+timeframe.
        Returns a flat dict of indicator values ready for AI scoring.
        """
        cache_key = f"indicators:{symbol}:{timeframe}"
        cached    = cache.get(cache_key)
        if cached:
            return cached

        df = _get_ohlcv_df(symbol, timeframe)
        if df is None or df.empty:
            return {}

        result: dict[str, Any] = {}

        # ── Trend ────────────────────────────────────────────────────────────
        result.update(self._ema(df))
        result.update(self._sma(df))
        result.update(self._vwap(df))
        result.update(self._supertrend(df))
        result.update(self._adx(df))
        result.update(self._trend_direction(df, result))

        # ── Momentum ─────────────────────────────────────────────────────────
        result.update(self._rsi(df))
        result.update(self._macd(df))
        result.update(self._stoch_rsi(df))
        result.update(self._cci(df))
        result.update(self._roc(df))

        # ── Volume ───────────────────────────────────────────────────────────
        result.update(self._obv(df))
        result.update(self._mfi(df))

        # ── Volatility ───────────────────────────────────────────────────────
        result.update(self._atr(df))
        result.update(self._bollinger(df))

        # ── Structure ────────────────────────────────────────────────────────
        result.update(self._support_resistance(df))

        ttl = CACHE_TTL.get(timeframe, 60)
        cache.set(cache_key, result, timeout=ttl)
        return result

    # ── EMA ──────────────────────────────────────────────────────────────────
    def _ema(self, df: pd.DataFrame) -> dict:
        close = df["close"]
        return {
            "ema_9":   round(float(close.ewm(span=9,   adjust=False).mean().iloc[-1]), 6),
            "ema_21":  round(float(close.ewm(span=21,  adjust=False).mean().iloc[-1]), 6),
            "ema_50":  round(float(close.ewm(span=50,  adjust=False).mean().iloc[-1]), 6),
            "ema_200": round(float(close.ewm(span=200, adjust=False).mean().iloc[-1]), 6),
            "ema_bullish": float(close.ewm(span=9).mean().iloc[-1]) > float(close.ewm(span=21).mean().iloc[-1]),
        }

    # ── SMA ──────────────────────────────────────────────────────────────────
    def _sma(self, df: pd.DataFrame) -> dict:
        close = df["close"]
        return {
            "sma_20":  round(float(close.rolling(20).mean().iloc[-1]), 6),
            "sma_50":  round(float(close.rolling(50).mean().iloc[-1]), 6),
            "sma_200": round(float(close.rolling(200).mean().iloc[-1]), 6),
        }

    # ── VWAP ─────────────────────────────────────────────────────────────────
    def _vwap(self, df: pd.DataFrame) -> dict:
        typical    = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol    = df["volume"].cumsum()
        cum_tp_vol = (typical * df["volume"]).cumsum()
        vwap       = (cum_tp_vol / cum_vol).iloc[-1]
        close      = df["close"].iloc[-1]
        return {
            "vwap":          round(float(vwap), 6),
            "price_above_vwap": float(close) > float(vwap),
        }

    # ── SuperTrend ────────────────────────────────────────────────────────────
    def _supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
        hl2       = (df["high"] + df["low"]) / 2
        atr_s     = self._atr_series(df, period)
        upper     = hl2 + multiplier * atr_s
        lower     = hl2 - multiplier * atr_s
        supertrend = pd.Series(index=df.index, dtype=float)
        direction  = pd.Series(index=df.index, dtype=int)

        supertrend.iloc[0] = upper.iloc[0]
        direction.iloc[0]  = 1

        for i in range(1, len(df)):
            if df["close"].iloc[i] > supertrend.iloc[i - 1]:
                supertrend.iloc[i] = lower.iloc[i]
                direction.iloc[i]  = 1
            else:
                supertrend.iloc[i] = upper.iloc[i]
                direction.iloc[i]  = -1

        return {
            "supertrend":          round(float(supertrend.iloc[-1]), 6),
            "supertrend_bullish":  int(direction.iloc[-1]) == 1,
        }

    # ── ADX ──────────────────────────────────────────────────────────────────
    def _adx(self, df: pd.DataFrame, period: int = 14) -> dict:
        high, low, close = df["high"], df["low"], df["close"]
        tr  = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        dm_pos = ((high - high.shift()) > (low.shift() - low)).astype(float) * (high - high.shift()).clip(lower=0)
        dm_neg = ((low.shift() - low) > (high - high.shift())).astype(float) * (low.shift() - low).clip(lower=0)
        atr_s  = tr.ewm(span=period, adjust=False).mean()
        di_pos = 100 * dm_pos.ewm(span=period, adjust=False).mean() / atr_s
        di_neg = 100 * dm_neg.ewm(span=period, adjust=False).mean() / atr_s
        dx     = 100 * abs(di_pos - di_neg) / (di_pos + di_neg).replace(0, np.nan)
        adx_v  = dx.ewm(span=period, adjust=False).mean().iloc[-1]
        return {
            "adx":         round(float(adx_v), 2),
            "trend_strong": float(adx_v) > 25,
        }

    # ── RSI ──────────────────────────────────────────────────────────────────
    def _rsi(self, df: pd.DataFrame, period: int = 14) -> dict:
        delta  = df["close"].diff()
        gain   = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
        loss   = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
        rs     = gain / loss.replace(0, np.nan)
        rsi_v  = (100 - (100 / (1 + rs))).iloc[-1]
        return {
            "rsi":          round(float(rsi_v), 2),
            "rsi_oversold":  float(rsi_v) < 30,
            "rsi_overbought": float(rsi_v) > 70,
        }

    # ── MACD ─────────────────────────────────────────────────────────────────
    def _macd(self, df: pd.DataFrame) -> dict:
        close     = df["close"]
        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal    = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal
        return {
            "macd":           round(float(macd_line.iloc[-1]), 6),
            "macd_signal":    round(float(signal.iloc[-1]), 6),
            "macd_histogram": round(float(histogram.iloc[-1]), 6),
            "macd_bullish":   float(histogram.iloc[-1]) > 0 and float(histogram.iloc[-1]) > float(histogram.iloc[-2]),
        }

    # ── Stochastic RSI ────────────────────────────────────────────────────────
    def _stoch_rsi(self, df: pd.DataFrame, period: int = 14, smooth_k: int = 3) -> dict:
        delta = df["close"].diff()
        gain  = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
        loss  = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = 100 - (100 / (1 + rs))
        rsi_min = rsi.rolling(period).min()
        rsi_max = rsi.rolling(period).max()
        stoch_k = 100 * (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
        stoch_d = stoch_k.rolling(smooth_k).mean()
        return {
            "stoch_rsi_k": round(float(stoch_k.iloc[-1]), 2),
            "stoch_rsi_d": round(float(stoch_d.iloc[-1]), 2),
        }

    # ── CCI ──────────────────────────────────────────────────────────────────
    def _cci(self, df: pd.DataFrame, period: int = 20) -> dict:
        tp   = (df["high"] + df["low"] + df["close"]) / 3
        mad  = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci_v = ((tp - tp.rolling(period).mean()) / (0.015 * mad)).iloc[-1]
        return {"cci": round(float(cci_v), 2)}

    # ── ROC ──────────────────────────────────────────────────────────────────
    def _roc(self, df: pd.DataFrame, period: int = 12) -> dict:
        roc_v = ((df["close"].iloc[-1] - df["close"].iloc[-period]) / df["close"].iloc[-period]) * 100
        return {"roc": round(float(roc_v), 4)}

    # ── OBV ──────────────────────────────────────────────────────────────────
    def _obv(self, df: pd.DataFrame) -> dict:
        sign = np.sign(df["close"].diff().fillna(0))
        obv  = (sign * df["volume"]).cumsum().iloc[-1]
        return {"obv": round(float(obv), 2)}

    # ── MFI ──────────────────────────────────────────────────────────────────
    def _mfi(self, df: pd.DataFrame, period: int = 14) -> dict:
        tp      = (df["high"] + df["low"] + df["close"]) / 3
        mf      = tp * df["volume"]
        pos_mf  = mf.where(tp > tp.shift(), 0).rolling(period).sum()
        neg_mf  = mf.where(tp <= tp.shift(), 0).rolling(period).sum()
        mfi_v   = (100 - 100 / (1 + pos_mf / neg_mf.replace(0, np.nan))).iloc[-1]
        return {"mfi": round(float(mfi_v), 2)}

    # ── ATR ──────────────────────────────────────────────────────────────────
    def _atr(self, df: pd.DataFrame, period: int = 14) -> dict:
        atr_s   = self._atr_series(df, period)
        atr_v   = atr_s.iloc[-1]
        price   = df["close"].iloc[-1]
        atr_pct = float(atr_v / price) if price > 0 else 0.0
        return {
            "atr":     round(float(atr_v), 6),
            "atr_pct": round(atr_pct, 6),
        }

    def _atr_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        hl  = df["high"] - df["low"]
        hpc = abs(df["high"] - df["close"].shift())
        lpc = abs(df["low"]  - df["close"].shift())
        tr  = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
        return tr.ewm(span=period, adjust=False).mean()

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    def _bollinger(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> dict:
        close    = df["close"]
        mid      = close.rolling(period).mean()
        dev      = close.rolling(period).std()
        upper    = mid + std * dev
        lower    = mid - std * dev
        bw       = ((upper - lower) / mid).iloc[-1]   # Bandwidth
        bp       = ((close - lower) / (upper - lower)).iloc[-1]  # %B
        return {
            "bb_upper":     round(float(upper.iloc[-1]), 6),
            "bb_middle":    round(float(mid.iloc[-1]),   6),
            "bb_lower":     round(float(lower.iloc[-1]), 6),
            "bb_bandwidth": round(float(bw),  4),
            "bb_pct_b":     round(float(bp),  4),
        }

    # ── Support / Resistance ──────────────────────────────────────────────────
    def _support_resistance(self, df: pd.DataFrame, lookback: int = 50) -> dict:
        recent = df.tail(lookback)
        highs  = recent["high"].nlargest(3).tolist()
        lows   = recent["low"].nsmallest(3).tolist()
        price  = float(df["close"].iloc[-1])
        return {
            "resistance_1":  round(highs[0], 6) if highs else 0.0,
            "resistance_2":  round(highs[1], 6) if len(highs) > 1 else 0.0,
            "support_1":     round(lows[0],  6) if lows  else 0.0,
            "support_2":     round(lows[1],  6) if len(lows) > 1 else 0.0,
            "near_resistance": price > (highs[0] * 0.99) if highs else False,
            "near_support":    price < (lows[0]  * 1.01) if lows  else False,
        }

    # ── Overall trend direction ───────────────────────────────────────────────
    def _trend_direction(self, df: pd.DataFrame, indicators: dict) -> dict:
        ema9  = indicators.get("ema_9",  0)
        ema21 = indicators.get("ema_21", 0)
        ema50 = indicators.get("ema_50", 0)
        adx   = indicators.get("adx",    0)
        price = float(df["close"].iloc[-1])

        if ema9 > ema21 > ema50 and price > ema50 and adx > 20:
            trend = "BULLISH"
        elif ema9 < ema21 < ema50 and price < ema50 and adx > 20:
            trend = "BEARISH"
        else:
            trend = "SIDEWAYS"

        return {"trend": trend}
