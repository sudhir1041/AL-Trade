"""
apps/ai_engine/tasks.py
-----------------------
T7 ✅  AI Decision Engine — 9-stage scoring pipeline.

Triggered by the Scanner worker for each candidate pair.
Output is persisted as AIScore and forwarded to the Strategy Engine.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.ai_engine")


@shared_task(bind=True, max_retries=2, queue="ai_scoring", name="apps.ai_engine.tasks.run_ai_scoring")
def run_ai_scoring(self, pair_id: str, scanner_factors: dict) -> dict:
    """
    T7 ✅  Full 9-stage AI pipeline for a single trading pair.
    """
    from apps.ai_engine.services import AIDecisionEngine
    try:
        engine = AIDecisionEngine()
        score  = engine.score_pair(pair_id, scanner_factors)
        logger.info(
            "AI scored %s: direction=%s confidence=%.1f",
            score.get("symbol"), score.get("direction"), score.get("confidence", 0),
        )
        # Forward to Strategy Engine if confidence is high enough
        if score.get("confidence", 0) >= 75 and score.get("direction") in ("BUY", "SELL"):
            from apps.strategies.tasks import evaluate_strategy_entry
            evaluate_strategy_entry.delay(ai_score_id=score["ai_score_id"])
        return score
    except Exception as exc:
        logger.exception("AI scoring failed for pair %s", pair_id)
        raise self.retry(exc=exc)


@shared_task(queue="ai_scoring", name="apps.ai_engine.tasks.refresh_watchlist_scores")
def refresh_watchlist_scores() -> None:
    """T7 ✅  Refresh AI scores for all watchlisted pairs every 5 minutes."""
    from apps.market.models import TradingPair
    pairs = TradingPair.objects.filter(is_active=True).values_list("id", flat=True)
    for pair_id in pairs:
        run_ai_scoring.delay(pair_id=str(pair_id), scanner_factors={})
