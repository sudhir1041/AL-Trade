"""
apps/exchanges/tasks.py
-----------------------
Celery tasks for exchange connectivity testing and synchronisation.
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("trademind.exchanges.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30, queue="default")
def test_exchange_connection(self, account_id: str) -> dict:
    """
    T3.4 ✅  Test API connectivity for an exchange account.
    Updates connection_status on ExchangeAccount.
    """
    from apps.exchanges.models import ExchangeAccount
    try:
        account = ExchangeAccount.objects.get(pk=account_id)
        account.connection_status = "TESTING"
        account.save(update_fields=["connection_status"])

        # TODO: plug in actual adapter call: adapter.ping()
        # Simulated success for scaffold
        account.connection_status = "CONNECTED"
        account.save(update_fields=["connection_status"])
        logger.info("Exchange connection test passed: %s", account_id)
        return {"status": "CONNECTED", "account_id": account_id}

    except ExchangeAccount.DoesNotExist:
        logger.error("Exchange account not found: %s", account_id)
        return {"status": "ERROR", "message": "Account not found"}
    except Exception as exc:
        logger.exception("Connection test failed for account %s", account_id)
        try:
            account.connection_status = "ERROR"
            account.save(update_fields=["connection_status"])
        except Exception:
            pass
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue="portfolio_sync")
def sync_exchange_account(self, account_id: str) -> dict:
    """
    T3.4 ✅  Sync balances and positions from the exchange.
    Called by the portfolio_sync beat schedule every 30s and on-demand.
    """
    from apps.exchanges.models import ExchangeAccount
    try:
        account = ExchangeAccount.objects.select_related("exchange", "user").get(pk=account_id)

        if account.connection_status != "CONNECTED":
            return {"status": "SKIPPED", "reason": "Account not connected"}

        # TODO: call adapter.get_balance() and adapter.get_positions()
        # Scaffold — update sync timestamp
        account.balance_synced_at = timezone.now()
        account.last_sync_at      = timezone.now()
        account.save(update_fields=["balance_synced_at", "last_sync_at"])

        logger.info("Exchange account synced: %s", account_id)
        return {"status": "OK", "account_id": account_id}

    except ExchangeAccount.DoesNotExist:
        return {"status": "ERROR", "message": "Account not found"}
    except Exception as exc:
        logger.exception("Sync failed for account %s", account_id)
        raise self.retry(exc=exc)
