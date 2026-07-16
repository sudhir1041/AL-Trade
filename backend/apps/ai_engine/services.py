"""
apps/ai_engine/services.py
--------------------------
T7 ✅  AI Decision Engine — 9-stage scoring pipeline implementation.

Stage 1: Data Integrity Validation
Stage 2: Liquidity Filter
Stage 3: Volatility Filter
Stage 4: Trend Detection
Stage 5: Momentum Evaluation
Stage 6: Multi-Timeframe Confirmation
Stage 7: Strategy Compatibility Validation
Stage 8: Risk Policy Validation
Stage 9: Recommendation Generation
"""

import logging
from typing import Any

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger("trademind.ai_engine.services")

# Confidence thresholds
THRESHOLD_AUTO      = 90   # ≥90 → eligible for full automation
THRESHOLD_HIGH      = 75   # ≥75 → high-quality watchlist
THRESHOLD_MONITOR   = 50   # ≥50 → monitor
THRESHOLD_IGNORE    = 0    # <50 → ignore


class AIDecisionEngine:
    """
    Stateless AI Decision Engine.
    Produces a recommendation for a single trading pair.
    """

    def score_pair(self, pair_id: str, scanner_factors: dict) -> dict:
        """Run all 9 stages and return a recommendation dict."""
        from apps.market.models import TradingPair
        from apps.ai_engine.models import AIScore, RecommendationDirection, RiskLevel

        try:
            pair = TradingPair.objects.select_related("exchange").get(pk=pair_id)
        except TradingPair.DoesNotExist:
            return {"error": "pair_not_found"}

        symbol = pair.symbol
        result = {
            "pair_id":   pair_id,
            "symbol":    symbol,
            "direction": RecommendationDirection.IGNORE,
            "confidence": 0.0,
            "risk_level": RiskLevel.HIGH,
            "supporting_factors": [],
            "conflicting_factors": [],
            "reasoning": "",
            "entry_zone_low":    None,
            "entry_zone_high":   None,
            "stop_loss_suggest": None,
            "tp1_suggest":       None,
            "tp2_suggest":       None,
            "risk_reward_ratio": None,
            "mtf_alignment":     {},
            "market_regime":     "",
            "compatible_strategies": [],
            "ai_score_id":       None,
        }

        # ── Stage 1: Data Integrity ───────────────────────────────────────────
        ticker = cache.get(f"ticker:{symbol}")
        if not ticker:
            result["reasoning"] = "Stage 1 FAIL: No live ticker data."
            return self._persist(result, pair)

        price = float(ticker.get("price", 0) or 0)
        if price <= 0:
            result["reasoning"] = "Stage 1 FAIL: Invalid price."
            return self._persist(result, pair)

        supporting = []
        conflicting = []
        score = 0.0

        # ── Stage 2: Liquidity Filter ─────────────────────────────────────────
        volume = float(ticker.get("volume_24h", 0) or 0)
        if volume < 500_000:
            result["reasoning"] = f"Stage 2 FAIL: Insufficient liquidity (${volume:,.0f})."
            return self._persist(result, pair)
        supporting.append("adequate_liquidity")

        # ── Stage 3: Volatility Filter ────────────────────────────────────────
        ind_1h = cache.get(f"indicators:{symbol}:1h") or {}
        atr_pct = float(ind_1h.get("atr_pct", 0.02) or 0.02)
        if atr_pct < 0.003 or atr_pct > 0.20:
            result["reasoning"] = f"Stage 3 FAIL: Volatility out of range ({atr_pct:.2%})."
            return self._persist(result, pair)
        supporting.append("volatility_in_range")
        score += 10

        # ── Stage 4: Trend Detection ──────────────────────────────────────────
        trend     = ind_1h.get("trend", "SIDEWAYS")
        adx       = float(ind_1h.get("adx", 0) or 0)
        supertrend_bull = ind_1h.get("supertrend_bullish", False)

        if trend == "BULLISH" and supertrend_bull:
            direction_vote = "BUY"
            score += 20
            supporting.append("strong_bullish_trend")
        elif trend == "BEARISH" and not supertrend_bull:
            direction_vote = "SELL"
            score += 15
            supporting.append("strong_bearish_trend")
        elif trend == "BULLISH":
            direction_vote = "BUY"
            score += 10
            supporting.append("bullish_trend")
        elif trend == "BEARISH":
            direction_vote = "SELL"
            score += 10
            supporting.append("bearish_trend")
        else:
            direction_vote = "HOLD"
            conflicting.append("sideways_market")

        if adx > 25:
            score += 8
            supporting.append("strong_adx")
        elif adx < 15:
            conflicting.append("weak_adx")

        # ── Stage 5: Momentum Evaluation ─────────────────────────────────────
        rsi      = float(ind_1h.get("rsi", 50) or 50)
        macd_bull = ind_1h.get("macd_bullish", False)
        macd_hist = float(ind_1h.get("macd_histogram", 0) or 0)

        if direction_vote == "BUY":
            if 40 <= rsi <= 65:
                score += 8
                supporting.append("rsi_momentum_buy")
            elif rsi < 35:
                score += 12
                supporting.append("rsi_oversold_bounce")
            elif rsi > 75:
                conflicting.append("rsi_overbought")
                score -= 5
        elif direction_vote == "SELL":
            if 35 <= rsi <= 60:
                score += 8
                supporting.append("rsi_momentum_sell")
            elif rsi > 65:
                score += 10
                supporting.append("rsi_overbought_reversal")

        if macd_bull and direction_vote == "BUY":
            score += 10
            supporting.append("macd_confirmation")
        elif not macd_bull and direction_vote == "SELL":
            score += 8
            supporting.append("macd_bearish_confirmation")

        # ── Stage 6: Multi-Timeframe Confirmation ─────────────────────────────
        mtf = {}
        mtf_score = 0
        for tf in ["5m", "15m", "4h"]:
            ind = cache.get(f"indicators:{symbol}:{tf}") or {}
            tf_trend = ind.get("trend", "SIDEWAYS")
            mtf[tf] = tf_trend
            if tf_trend == trend:
                mtf_score += 1

        result["mtf_alignment"] = mtf

        if mtf_score >= 2:
            score += 12
            supporting.append("mtf_aligned")
        elif mtf_score == 0:
            conflicting.append("mtf_conflict")
            score -= 8

        # ── Stage 7: Strategy Compatibility ──────────────────────────────────
        compatible = []
        if trend in ("BULLISH", "BEARISH") and adx > 20:
            compatible.append("trend_following")
        if ind_1h.get("bb_pct_b", 0.5) < 0.2:
            compatible.append("mean_reversion")
        if ind_1h.get("volume_spike", False):
            compatible.append("momentum")
            compatible.append("breakout")
            score += 5
            supporting.append("volume_spike")

        result["compatible_strategies"] = compatible

        # ── Stage 8: Risk Assessment ──────────────────────────────────────────
        support_1    = float(ind_1h.get("support_1", price * 0.97) or price * 0.97)
        resistance_1 = float(ind_1h.get("resistance_1", price * 1.03) or price * 1.03)
        atr          = float(ind_1h.get("atr", price * atr_pct) or price * atr_pct)

        if direction_vote == "BUY":
            sl     = round(support_1 - atr * 0.5, 8)
            tp1    = round(price + atr * 1.5, 8)
            tp2    = round(price + atr * 3.0, 8)
            rr     = round((tp1 - price) / (price - sl), 2) if price > sl else 0
        elif direction_vote == "SELL":
            sl     = round(resistance_1 + atr * 0.5, 8)
            tp1    = round(price - atr * 1.5, 8)
            tp2    = round(price - atr * 3.0, 8)
            rr     = round((price - tp1) / (sl - price), 2) if sl > price else 0
        else:
            sl = tp1 = tp2 = rr = None

        result.update({
            "entry_zone_low":    round(price * 0.999, 8),
            "entry_zone_high":   round(price * 1.001, 8),
            "stop_loss_suggest": sl,
            "tp1_suggest":       tp1,
            "tp2_suggest":       tp2,
            "risk_reward_ratio": rr,
        })

        if rr and rr < 1.5:
            conflicting.append("poor_risk_reward")
            score -= 5
        elif rr and rr >= 2.0:
            supporting.append("good_risk_reward")
            score += 5

        # ── Stage 9: Final Recommendation ────────────────────────────────────
        score = max(0.0, min(100.0, score))

        if score >= THRESHOLD_AUTO and direction_vote in ("BUY", "SELL"):
            final_direction = direction_vote
            risk_level      = "LOW"
        elif score >= THRESHOLD_HIGH and direction_vote in ("BUY", "SELL"):
            final_direction = direction_vote
            risk_level      = "MEDIUM"
        elif score >= THRESHOLD_MONITOR and direction_vote in ("BUY", "SELL"):
            final_direction = "HOLD"
            risk_level      = "MEDIUM"
        else:
            final_direction = "IGNORE"
            risk_level      = "HIGH"

        # Build human-readable reasoning
        reasoning_parts = []
        if supporting:
            reasoning_parts.append(f"Positive signals: {', '.join(supporting[:5])}.")
        if conflicting:
            reasoning_parts.append(f"Concerns: {', '.join(conflicting[:3])}.")
        reasoning_parts.append(
            f"Trend: {trend} | RSI: {rsi:.1f} | ADX: {adx:.1f} | "
            f"MTF aligned: {mtf_score}/3 | Score: {score:.1f}/100."
        )

        result.update({
            "direction":          final_direction,
            "confidence":         round(score, 2),
            "risk_level":         risk_level,
            "market_regime":      self._classify_regime(ind_1h, trend),
            "supporting_factors": supporting,
            "conflicting_factors": conflicting,
            "reasoning":          " ".join(reasoning_parts),
        })

        return self._persist(result, pair)

    def _classify_regime(self, ind: dict, trend: str) -> str:
        adx     = float(ind.get("adx", 0) or 0)
        atr_pct = float(ind.get("atr_pct", 0.02) or 0.02)
        if atr_pct > 0.08:
            return "HIGH_VOL"
        if adx > 30 and trend == "BULLISH":
            return "STRONG_BULL"
        if adx > 20 and trend == "BULLISH":
            return "WEAK_BULL"
        if adx > 30 and trend == "BEARISH":
            return "STRONG_BEAR"
        if adx > 20 and trend == "BEARISH":
            return "WEAK_BEAR"
        return "SIDEWAYS"

    def _persist(self, result: dict, pair) -> dict:
        """Persist AIScore to database and return result with ai_score_id."""
        from apps.ai_engine.models import AIScore
        try:
            score_obj = AIScore.objects.create(
                trading_pair=pair,
                confidence_score=result["confidence"],
                risk_score=self._risk_score(result["risk_level"]),
                direction=result["direction"],
                risk_level=result["risk_level"],
                market_regime=result.get("market_regime", ""),
                entry_zone_low=result.get("entry_zone_low"),
                entry_zone_high=result.get("entry_zone_high"),
                stop_loss_suggest=result.get("stop_loss_suggest"),
                tp1_suggest=result.get("tp1_suggest"),
                tp2_suggest=result.get("tp2_suggest"),
                risk_reward_ratio=result.get("risk_reward_ratio"),
                supporting_factors=result.get("supporting_factors", []),
                conflicting_factors=result.get("conflicting_factors", []),
                reasoning=result.get("reasoning", ""),
                mtf_alignment=result.get("mtf_alignment", {}),
                compatible_strategies=result.get("compatible_strategies", []),
            )
            result["ai_score_id"] = str(score_obj.id)
        except Exception:
            logger.exception("Failed to persist AIScore for %s", result.get("symbol"))
        return result

    @staticmethod
    def _risk_score(risk_level: str) -> float:
        return {"LOW": 20.0, "MEDIUM": 50.0, "HIGH": 75.0, "EXTREME": 95.0}.get(risk_level, 50.0)
