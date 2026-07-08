"""
apps/notifications/views.py
T14 ✅  Notification REST endpoints.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from django.utils import timezone
from core.responses import error_response, success_response
from common.utils import paginate_queryset
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /api/v1/notifications/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs   = Notification.objects.filter(user=request.user, deleted_at__isnull=True).order_by("-created_at")
        unread = qs.filter(is_read=False).count()
        page   = int(request.query_params.get("page", 1))
        paged  = paginate_queryset(qs, page, 30)
        return success_response(
            data=NotificationSerializer(paged["results"], many=True).data,
            meta={"unread": unread, "total": paged["count"]},
        )


class NotificationMarkReadView(APIView):
    """PATCH /api/v1/notifications/read/  — mark all unread as read"""
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request):
        ids = request.data.get("ids")   # optional list of IDs; null = mark all
        qs  = Notification.objects.filter(user=request.user, is_read=False)
        if ids:
            qs = qs.filter(id__in=ids)
        count = qs.update(is_read=True, read_at=timezone.now())
        return success_response(message=f"{count} notification(s) marked as read.")


class NotificationDeleteView(APIView):
    """DELETE /api/v1/notifications/{id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, pk: str):
        try:
            n = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return error_response("RESOURCE_NOT_FOUND", "Notification not found.", status_code=404)
        n.soft_delete(deleted_by=request.user.id)
        return success_response(message="Notification deleted.")
