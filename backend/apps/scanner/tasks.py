"""
apps/scanner/tasks.py
---------------------
T5 ✅  Market Scanner Celery tasks.

The scanner runs every 60 seconds (configured in config/celery.py beat_schedule).
It evaluates all active trading pairs and forwards high-confidence candidates
to the AI Decision Engine via internal events.
"""

import logging
from datetime import datetime, timezone as tz

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("trademind.scanner")


@shared_task(bind=True, max_retries=2, queue="scanner", name="apps.scanner.tasks.run_market_scan")
def run_market_scan(self, user_id: str | None = None) -> dict:
    """
    Main scanner task — runs continuously every 60 seconds.

    Pipeline:
    1. Load all active trading pairs
    2. Pull cached ticker + indicator data from Redis
    3. Apply filters (volume, spread, volatility, trend, RSI, MACD)
    4. Score each pair (confidence 0–100)
    5. Persist ScannerJob + ScannerResult rows
    6. Publish candidates to AI engine queue
    """
    from apps.scanner.models import ScannerJob, ScannerResult, ScannerSettings
    from apps.market.models import TradingPair, Ticker
    from apps.scanner.services import ScannerService

    started_at = timezone.now()
    job = ScannerJob.objects.create(
        tenant_id=_system_tenant_id(),
        status="RUNNING",
        started_at=started_at,
    )

    try:
        service   = ScannerService()
        pairs     = TradingPair.objects.filter(is_active=True).select_related("exchange")
        results   = service.scan_all(pairs)

        candidates_found = 0
        for result in results:
            ScannerResult.objects.create(
                scanner_job=job,
                trading_pair_id=result["pair_id"],
                tenant_id=_system_tenant_id(),
                confidence_score=result["confidence"],
                risk_score=result["risk"],
                trend_direction=result["trend"],
                volume_24h_usdt=result["volume"],
                volume_spike=result["volume_spike"],
                spread_pct=result["spread"],
                btc_correlation=result["btc_corr"],
                eth_correlation=result["eth_corr"],
                factors=result["factors"],
                is_candidate=result["is_candidate"],
                rejection_reason=result.get("rejection_reason", ""),
            )
            if result["is_candidate"]:
                candidates_found += 1
                # Forward to AI engine
                score_candidate.delay(
                    pair_id=result["pair_id"],
                    scanner_factors=result["factors"],
                )

        duration_ms = int((timezone.now() - started_at).total_seconds() * 1000)
        job.status           = "COMPLETED"
        job.completed_at     = timezone.now()
        job.pairs_scanned    = len(results)
        job.candidates_found = candidates_found
        job.rejected_count   = len(results) - candidates_found
        job.duration_ms      = duration_ms
        job.save(update_fields=[
            "status", "completed_at", "pairs_scanned",
            "candidates_found", "rejected_count", "duration_ms",
        ])

        logger.info(
            "Scanner completed: %d pairs scanned, %d candidates in %dms",
            len(results), candidates_found, duration_ms,
        )
        return {"status": "OK", "pairs": len(results), "candidates": candidates_found}

    except Exception as exc:
        job.status        = "FAILED"
        job.completed_at  = timezone.now()
        job.error_message = str(exc)
        job.save(update_fields=["status", "completed_at", "error_message"])
        logger.exception("Scanner task failed")
        raise self.retry(exc=exc)


@shared_task(queue="ai_scoring", name="apps.scanner.tasks.score_candidate")
def score_candidate(pair_id: str, scanner_factors: dict) -> None:
    """Forward a scanner candidate to the AI Decision Engine for full scoring."""
    from apps.ai_engine.tasks import run_ai_scoring
    run_ai_scoring.delay(pair_id=pair_id, scanner_factors=scanner_factors)


def _system_tenant_id():
    """Return a fixed UUID used for system-generated (non-user) records."""
    import uuid
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
