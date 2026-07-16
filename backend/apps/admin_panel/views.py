"""
apps/admin_panel/views.py
T16.11 ✅  Admin panel endpoints.
Only accessible to ADMIN / SUPER_ADMIN roles.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from core.permissions import IsAdminUser
from core.responses import error_response, success_response
from common.utils import paginate_queryset


class AdminUserListView(APIView):
    """GET /api/v1/admin/users/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        from apps.accounts.models import User
        qs     = User.objects.all().order_by("-date_joined")
        search = request.query_params.get("search", "")
        role   = request.query_params.get("role", "")
        if search:
            qs = qs.filter(email__icontains=search) | qs.filter(username__icontains=search)
        if role:
            qs = qs.filter(role=role.upper())
        paged  = paginate_queryset(qs, int(request.query_params.get("page", 1)), 50)
        data   = list(paged["results"].values(
            "id", "email", "username", "role", "is_active", "date_joined"
        ))
        return success_response(data=data, meta={"total": paged["count"]})


class AdminUserDetailView(APIView):
    """PATCH/DELETE /api/v1/admin/users/{id}/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request: Request, pk: str):
        from apps.accounts.models import User
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "User not found.", status_code=404)
        allowed = {"is_active", "role"}
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save(update_fields=[f for f in allowed if f in request.data])
        return success_response(message="User updated.")

    def delete(self, request: Request, pk: str):
        from apps.accounts.models import User
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "User not found.", status_code=404)
        user.is_active = False
        user.save(update_fields=["is_active"])
        return success_response(message="User deactivated.")


class AdminSystemView(APIView):
    """GET /api/v1/admin/system/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        from apps.accounts.models import User
        from apps.orders.models import Order, Position, OrderStatus, PositionStatus
        from apps.exchanges.models import ExchangeAccount
        return success_response(data={
            "total_users":     User.objects.count(),
            "active_users":    User.objects.filter(is_active=True).count(),
            "open_positions":  Position.objects.filter(status=PositionStatus.OPEN).count(),
            "open_orders":     Order.objects.filter(status=OrderStatus.SUBMITTED).count(),
            "connected_exchanges": ExchangeAccount.objects.filter(
                connection_status="CONNECTED", is_active=True
            ).count(),
        })


class AdminWorkerStatusView(APIView):
    """GET /api/v1/admin/workers/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        try:
            from config.celery import app
            inspect   = app.control.inspect(timeout=2)
            active    = inspect.active()  or {}
            reserved  = inspect.reserved() or {}
            stats     = inspect.stats()    or {}
            workers   = [
                {
                    "worker":   name,
                    "active":   len(tasks),
                    "reserved": len(reserved.get(name, [])),
                    "status":   "online",
                }
                for name, tasks in active.items()
            ]
        except Exception:
            workers = []
        return success_response(data={"workers": workers})


class AdminQueueStatusView(APIView):
    """GET /api/v1/admin/queues/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        from django.core.cache import cache
        queues = [
            "default", "scanner", "ai_scoring", "notifications",
            "reports", "ml_training", "portfolio_sync", "order_sync", "backtest",
        ]
        data = [{"queue": q, "size": cache.get(f"queue_size:{q}", 0)} for q in queues]
        return success_response(data={"queues": data})


class AdminLogsView(APIView):
    """GET /api/v1/admin/logs/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        from apps.accounts.models import AuditLog
        qs    = AuditLog.objects.order_by("-created_at")
        paged = paginate_queryset(qs, int(request.query_params.get("page", 1)), 50)
        data  = list(paged["results"].values(
            "id", "action", "resource_type", "resource_id",
            "ip_address", "user_id", "created_at"
        ))
        return success_response(data=data, meta={"total": paged["count"]})


class AdminSettingsView(APIView):
    """GET/PATCH /api/v1/admin/settings/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request: Request):
        return success_response(data={
            "maintenance_mode":    False,
            "registration_open":  True,
            "scanner_enabled":    True,
            "ai_enabled":         True,
        })
