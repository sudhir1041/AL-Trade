"""
apps/exchanges/views.py
-----------------------
Exchange integration API views.
GET /exchanges                    – list supported exchanges
GET/POST /exchange-accounts       – list user accounts / add new
GET/PATCH/DELETE /exchange-accounts/{id}
POST /exchange-accounts/{id}/test  – test connectivity
POST /exchange-accounts/{id}/sync  – trigger manual sync
GET  /exchange-accounts/{id}/balances
GET  /exchange-accounts/{id}/positions
GET  /exchange-accounts/{id}/orders
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.permissions import IsTenantMember, IsOwnerOrAdmin
from core.responses import (
    created_response, error_response, no_content_response, success_response
)
from .models import Exchange, ExchangeAccount
from .serializers import (
    ExchangeAccountCreateSerializer,
    ExchangeAccountSerializer,
    ExchangeAccountUpdateSerializer,
    ExchangeSerializer,
)

logger = logging.getLogger("trademind.exchanges")


# ─────────────────────────────────────────────────────────────────────────────
# T3.2 ✅  List all supported exchanges
# ─────────────────────────────────────────────────────────────────────────────
class ExchangeListView(APIView):
    """GET /api/v1/exchanges/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        exchanges = Exchange.objects.filter(is_active=True).order_by("phase", "name")
        return success_response(
            data=ExchangeSerializer(exchanges, many=True).data,
            message="Supported exchanges retrieved.",
        )


class ExchangeDetailView(APIView):
    """GET /api/v1/exchanges/{id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str):
        try:
            exchange = Exchange.objects.get(pk=pk, is_active=True)
        except Exchange.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Exchange not found.", status_code=404)
        return success_response(data=ExchangeSerializer(exchange).data)


# ─────────────────────────────────────────────────────────────────────────────
# T3.4 ✅  Exchange Account CRUD
# ─────────────────────────────────────────────────────────────────────────────
class ExchangeAccountListCreateView(APIView):
    """
    GET  /api/v1/exchange-accounts/   – list user's connected accounts
    POST /api/v1/exchange-accounts/   – connect a new exchange account
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        accounts = ExchangeAccount.objects.filter(
            user=request.user,
            deleted_at__isnull=True,
        ).select_related("exchange").order_by("-created_at")
        return success_response(
            data=ExchangeAccountSerializer(accounts, many=True).data,
            message=f"{accounts.count()} exchange account(s) found.",
        )

    def post(self, request: Request):
        serializer = ExchangeAccountCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "VALIDATION_ERROR", "Invalid exchange credentials.",
                details={"field_errors": serializer.errors},
            )
        account = serializer.save(
            user=request.user,
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        logger.info("Exchange account connected: user=%s exchange=%s", request.user.id, account.exchange_id)
        return created_response(
            data=ExchangeAccountSerializer(account).data,
            message="Exchange account connected. Testing connectivity...",
        )


class ExchangeAccountDetailView(APIView):
    """
    GET    /api/v1/exchange-accounts/{id}/
    PATCH  /api/v1/exchange-accounts/{id}/
    DELETE /api/v1/exchange-accounts/{id}/
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def _get_account(self, pk: str, user) -> ExchangeAccount | None:
        try:
            return ExchangeAccount.objects.get(pk=pk, user=user, deleted_at__isnull=True)
        except ExchangeAccount.DoesNotExist:
            return None

    def get(self, request: Request, pk: str):
        account = self._get_account(pk, request.user)
        if not account:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)
        return success_response(data=ExchangeAccountSerializer(account).data)

    def patch(self, request: Request, pk: str):
        account = self._get_account(pk, request.user)
        if not account:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)

        serializer = ExchangeAccountUpdateSerializer(account, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Update failed.", details=serializer.errors)
        serializer.save(updated_by=request.user.id)
        return success_response(
            data=ExchangeAccountSerializer(account).data,
            message="Exchange account updated.",
        )

    def delete(self, request: Request, pk: str):
        account = self._get_account(pk, request.user)
        if not account:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)
        account.soft_delete(deleted_by=request.user.id)
        logger.info("Exchange account disconnected: user=%s account=%s", request.user.id, pk)
        return no_content_response("Exchange account removed.")


# ─────────────────────────────────────────────────────────────────────────────
# T3.4 ✅  Test & Sync
# ─────────────────────────────────────────────────────────────────────────────
class ExchangeAccountTestView(APIView):
    """POST /api/v1/exchange-accounts/{id}/test/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            account = ExchangeAccount.objects.get(pk=pk, user=request.user)
        except ExchangeAccount.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)

        # Queue connectivity test as a background task
        from apps.exchanges.tasks import test_exchange_connection
        test_exchange_connection.delay(str(account.id))

        return success_response(message="Connection test initiated. Check status in a moment.")


class ExchangeAccountSyncView(APIView):
    """POST /api/v1/exchange-accounts/{id}/sync/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            account = ExchangeAccount.objects.get(pk=pk, user=request.user)
        except ExchangeAccount.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)

        from apps.exchanges.tasks import sync_exchange_account
        sync_exchange_account.delay(str(account.id))

        return success_response(message="Sync initiated. Balance and positions will update shortly.")


class ExchangeAccountBalancesView(APIView):
    """GET /api/v1/exchange-accounts/{id}/balances/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str):
        try:
            account = ExchangeAccount.objects.get(pk=pk, user=request.user)
        except ExchangeAccount.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Exchange account not found.", status_code=404)

        from apps.portfolio.models import Portfolio, PortfolioAsset
        try:
            portfolio = Portfolio.objects.get(exchange_account=account)
            assets    = PortfolioAsset.objects.filter(portfolio=portfolio).order_by("-value_usdt")
            assets_data = [
                {
                    "asset":          a.asset,
                    "quantity":       str(a.quantity),
                    "current_price":  str(a.current_price),
                    "value_usdt":     str(a.value_usdt),
                    "allocation_pct": str(a.allocation_pct),
                    "unrealized_pnl": str(a.unrealized_pnl),
                }
                for a in assets
            ]
            return success_response(data={
                "total_balance":     str(portfolio.total_balance),
                "available_balance": str(portfolio.available_balance),
                "unrealized_pnl":    str(portfolio.unrealized_pnl),
                "assets":            assets_data,
                "last_synced_at":    portfolio.last_synced_at.isoformat() if portfolio.last_synced_at else None,
            })
        except Portfolio.DoesNotExist:
            return success_response(data={"total_balance": "0", "assets": []},
                                     message="No balance data yet. Try syncing the account.")
