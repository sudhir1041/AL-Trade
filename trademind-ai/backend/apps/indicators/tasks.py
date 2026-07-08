"""
apps/indicators/tasks.py
------------------------
T6 ✅  Celery tasks for indicator calculation.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.indicators.tasks")


@shared_task(queue="ai_scoring", name="apps.indicators.tasks.calculate_indicators")
def calculate_indicators(symbol: str, timeframe: str = "1h") -> dict:
    """Calculate and cache all indicators for a symbol+timeframe."""
    from apps.indicators.engine import IndicatorEngine
    engine = IndicatorEngine()
    result = engine.compute_all(symbol, timeframe)
    logger.debug("Indicators computed: %s %s — %d values", symbol, timeframe, len(result))
    return result


@shared_task(queue="ai_scoring", name="apps.indicators.tasks.calculate_all_timeframes")
def calculate_all_timeframes(symbol: str) -> None:
    """Calculate indicators across all timeframes for multi-timeframe analysis."""
    for tf in ["5m", "15m", "1h", "4h", "1d"]:
        calculate_indicators.delay(symbol, tf)
