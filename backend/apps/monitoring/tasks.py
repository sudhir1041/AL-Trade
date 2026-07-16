"""
apps/monitoring/tasks.py
T1.4 ✅  Cleanup + maintenance tasks.
"""
import logging
from celery import shared_task

logger = logging.getLogger("trademind.monitoring.tasks")


@shared_task(queue="default", name="apps.monitoring.tasks.cleanup_old_data")
def cleanup_old_data() -> dict:
    """T1.4 ✅  Daily cleanup — remove stale data to keep DB lean."""
    from django.utils import timezone
    from datetime import timedelta

    cutoff_30d = timezone.now() - timedelta(days=30)
    cutoff_7d  = timezone.now() - timedelta(days=7)

    deleted = {}

    # Clean expired email verification tokens
    from apps.accounts.models import EmailVerificationToken, PasswordResetToken
    r = EmailVerificationToken.objects.filter(expires_at__lt=cutoff_7d, is_used=True).delete()
    deleted["expired_verification_tokens"] = r[0]

    r = PasswordResetToken.objects.filter(expires_at__lt=cutoff_7d).delete()
    deleted["expired_reset_tokens"] = r[0]

    # Clean old ticker data (keep 1 day)
    from apps.market.models import Ticker
    cutoff_1d = timezone.now() - timedelta(days=1)
    r = Ticker.objects.filter(created_at__lt=cutoff_1d).delete()
    deleted["old_tickers"] = r[0]

    # Clean old scanner results (keep 7 days)
    from apps.scanner.models import ScannerResult
    r = ScannerResult.objects.filter(created_at__lt=cutoff_7d).delete()
    deleted["old_scanner_results"] = r[0]

    logger.info("Cleanup completed: %s", deleted)
    return {"deleted": deleted}
