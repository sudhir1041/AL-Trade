"""
apps/orders/views.py
--------------------
T11 ✅  Order Management API — Vol.5 §13.

POST   /orders/                   – place order (goes through Risk Engine first)
GET    /orders/                   – list orders
GET    /orders/{id}/              – order detail
PATCH  /orders/{id}/              – modify (change SL/TP)
DELETE /orders/{id}/              – cancel order
GET    /positions/                – list open positions
GET    /positions/{id}/           – position detail
POST   /positions/{id}/close/     – close full position
POST   /positions/{id}/partial-close/ – partial close
GET    /trades/                   – trade history
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import (
    created_response, error_response, success_response, paginated_response
)
from common.utils import paginate_queryset
from .models import Order, OrderStatus, Position, PositionStatus
from .serializers import OrderCreateSerializer, OrderSerializer, PositionSerializer

logger = logging.getLogger("trademind.orders.views")


class OrderListCreateView(APIView):
    """POST /api/v1/orders/  |  GET /api/v1/orders/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = (
            Order.objects.filter(user=request.user, deleted_at__isnull=True)
            .select_related("trading_pair", "exchange_account__exchange", "strategy")
            .order_by("-created_at")
        )
        # Filters
        sym    = request.query_params.get("symbol")
        st     = request.query_params.get("status")
        paper  = request.query_params.get("paper")
        if sym:    qs = qs.filter(trading_pair__symbol=sym.upper())
        if st:     qs = qs.filter(status=st.upper())
        if paper is not None:
            qs = qs.filter(is_paper_trade=(paper.lower() == "true"))

        page      = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        paged     = paginate_queryset(qs, page, page_size)

        return paginated_response(
            data=OrderSerializer(paged["results"], many=True).data,
            page=page, page_size=page_size,
            total_count=paged["count"],
            message=f"{paged['count']} order(s) found.",
        )

    def post(self, request: Request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid order data.",
                                   details={"field_errors": serializer.errors})

        data = serializer.validated_data

        # ── Risk Engine validation (T10) ──────────────────────────────────────
        from apps.risk.services import RiskEngine
        risk = RiskEngine()
        result = risk.validate_order(
            user=request.user,
            exchange_account=data["exchange_account"],
            trading_pair_symbol=data["trading_pair"].symbol,
            side=data["side"],
            quantity=float(data["quantity"]),
            entry_price=float(data.get("price") or 0),
            stop_loss_price=float(data.get("stop_loss_price") or 0),
            is_paper_trade=data.get("is_paper_trade", False),
        )
        if not result:
            # Log the violation
            from apps.risk.models import RiskViolationLog
            RiskViolationLog.objects.create(
                user=request.user,
                rule_name=result.rule,
                order_data={
                    "symbol": data["trading_pair"].symbol,
                    "side":   data["side"],
                    "qty":    str(data["quantity"]),
                },
            )
            return error_response(
                "ORDER_REJECTED",
                f"Order rejected by Risk Engine: {result.message}",
                details={"rule": result.rule},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ── Create order ──────────────────────────────────────────────────────
        import uuid
        order = Order.objects.create(
            **data,
            user=request.user,
            tenant_id=request.user.tenant_id or request.user.id,
            client_order_id=str(uuid.uuid4()),
            idempotency_key=data.get("idempotency_key") or str(uuid.uuid4()),
            created_by=request.user.id,
        )

        # ── Submit to exchange asynchronously ─────────────────────────────────
        if not order.is_paper_trade:
            from apps.orders.tasks import submit_order_to_exchange
            submit_order_to_exchange.delay(str(order.id))
        else:
            from apps.orders.tasks import simulate_paper_order
            simulate_paper_order.delay(str(order.id))

        logger.info("Order created: %s %s %s qty=%s user=%s",
                    order.side, order.trading_pair.symbol, order.order_type,
                    order.quantity, request.user.id)

        return created_response(
            data=OrderSerializer(order).data,
            message="Order placed and queued for execution.",
        )


class OrderDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/orders/{id}/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return Order.objects.get(pk=pk, user=user)
        except Order.DoesNotExist:
            return None

    def get(self, request: Request, pk: str):
        order = self._get(pk, request.user)
        if not order:
            return error_response("RESOURCE_NOT_FOUND", "Order not found.", status_code=404)
        return success_response(data=OrderSerializer(order).data)

    def patch(self, request: Request, pk: str):
        order = self._get(pk, request.user)
        if not order:
            return error_response("RESOURCE_NOT_FOUND", "Order not found.", status_code=404)
        if order.is_complete:
            return error_response("ORDER_COMPLETE", "Cannot modify a completed order.")
        # Only SL/TP modification allowed after order creation
        allowed = {k: v for k, v in request.data.items()
                   if k in ("stop_loss_price", "take_profit_price")}
        for field, value in allowed.items():
            setattr(order, field, value)
        order.save(update_fields=list(allowed.keys()))
        return success_response(data=OrderSerializer(order).data, message="Order updated.")

    def delete(self, request: Request, pk: str):
        order = self._get(pk, request.user)
        if not order:
            return error_response("RESOURCE_NOT_FOUND", "Order not found.", status_code=404)
        if order.is_complete:
            return error_response("ORDER_COMPLETE", "Cannot cancel a completed order.")
        from apps.orders.tasks import cancel_order_on_exchange
        cancel_order_on_exchange.delay(str(order.id))
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return success_response(message="Order cancellation requested.")


class PositionListView(APIView):
    """GET /api/v1/positions/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = (
            Position.objects.filter(user=request.user, status=PositionStatus.OPEN)
            .select_related("trading_pair", "exchange_account__exchange", "strategy")
            .order_by("-opened_at")
        )
        paper = request.query_params.get("paper")
        if paper is not None:
            qs = qs.filter(is_paper_trade=(paper.lower() == "true"))
        return success_response(
            data=PositionSerializer(qs, many=True).data,
            meta={"open_count": qs.count()},
        )


class PositionDetailView(APIView):
    """GET /api/v1/positions/{id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str):
        try:
            pos = Position.objects.get(pk=pk, user=request.user)
        except Position.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Position not found.", status_code=404)
        return success_response(data=PositionSerializer(pos).data)


class PositionCloseView(APIView):
    """POST /api/v1/positions/{id}/close/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        try:
            pos = Position.objects.get(pk=pk, user=request.user, status=PositionStatus.OPEN)
        except Position.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Open position not found.", status_code=404)
        from apps.orders.tasks import close_position
        close_position.delay(str(pos.id), partial=False)
        return success_response(message="Position close order queued.")


class PositionPartialCloseView(APIView):
    """POST /api/v1/positions/{id}/partial-close/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str):
        pct = float(request.data.get("close_pct", 50))
        if not (1 <= pct <= 99):
            return error_response("VALIDATION_ERROR", "close_pct must be between 1 and 99.")
        try:
            pos = Position.objects.get(pk=pk, user=request.user, status=PositionStatus.OPEN)
        except Position.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Open position not found.", status_code=404)
        from apps.orders.tasks import close_position
        close_position.delay(str(pos.id), partial=True, close_pct=pct)
        return success_response(message=f"Partial close ({pct}%) queued.")


class TradeHistoryView(APIView):
    """GET /api/v1/trades/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = (
            Order.objects.filter(user=request.user, status=OrderStatus.FILLED)
            .select_related("trading_pair", "exchange_account__exchange", "strategy")
            .order_by("-filled_at")
        )
        page      = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        paged     = paginate_queryset(qs, page, page_size)
        return paginated_response(
            data=OrderSerializer(paged["results"], many=True).data,
            page=page, page_size=page_size,
            total_count=paged["count"],
        )
