"""
apps/users/views.py
-------------------
T2.3 ✅  User profile & preferences endpoints (Vol.5 §5).

GET  /users/me/           – full profile
PATCH /users/me/          – update name/timezone/language
GET  /users/preferences/  – notification & trading preferences
PATCH /users/preferences/ – update preferences
GET  /users/security/     – 2FA status + active devices
GET  /users/activity/     – recent audit log entries
"""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.request import Request
from rest_framework.views import APIView

from core.responses import error_response, success_response
from .models import UserProfile, UserPreferences
from .serializers import (
    UserMeSerializer, UserPreferencesSerializer,
    UserProfileSerializer, UserActivitySerializer,
)

logger = logging.getLogger("trademind.users.views")


class UserMeView(APIView):
    """GET /api/v1/users/me/  |  PATCH /api/v1/users/me/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        return success_response(data=UserMeSerializer(request.user).data)

    def patch(self, request: Request):
        # Update User fields
        user   = request.user
        allowed = {"first_name", "last_name", "timezone", "language", "preferred_currency", "username"}
        update  = {k: v for k, v in request.data.items() if k in allowed}
        for field, value in update.items():
            setattr(user, field, value)
        if update:
            user.save(update_fields=list(update.keys()))

        # Update profile fields
        profile_fields = {"bio", "phone_number", "country", "city"}
        profile_data   = {k: v for k, v in request.data.items() if k in profile_fields}
        if profile_data:
            UserProfile.objects.update_or_create(user=user, defaults=profile_data)

        return success_response(data=UserMeSerializer(user).data, message="Profile updated.")


class UserProfilePictureView(APIView):
    """PATCH /api/v1/users/me/picture/"""
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser]

    def patch(self, request: Request):
        picture = request.FILES.get("picture")
        if not picture:
            return error_response("VALIDATION_ERROR", "No picture file provided.")
        if picture.size > 5 * 1024 * 1024:   # 5MB limit
            return error_response("VALIDATION_ERROR", "Picture must be under 5MB.")

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.profile_picture = picture
        profile.save(update_fields=["profile_picture"])
        return success_response(message="Profile picture updated.")


class UserPreferencesView(APIView):
    """GET /api/v1/users/preferences/  |  PATCH /api/v1/users/preferences/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
        return success_response(data=UserPreferencesSerializer(prefs).data)

    def patch(self, request: Request):
        prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(prefs, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Invalid preferences.", details=serializer.errors)
        serializer.save()
        return success_response(data=serializer.data, message="Preferences updated.")


class UserSecurityView(APIView):
    """GET /api/v1/users/security/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from apps.accounts.models import UserDevice, RefreshTokenRecord
        from django.utils import timezone

        devices = list(
            request.user.devices.order_by("-last_seen")[:10].values(
                "device_id", "device_name", "device_type", "last_ip", "last_seen", "is_trusted"
            )
        )
        active_sessions = RefreshTokenRecord.objects.filter(
            user=request.user,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).count()

        return success_response(data={
            "is_2fa_enabled":   request.user.is_2fa_enabled,
            "active_sessions":  active_sessions,
            "devices":          devices,
        })


class UserActivityView(APIView):
    """GET /api/v1/users/activity/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from apps.accounts.models import AuditLog
        logs = AuditLog.objects.filter(
            user=request.user
        ).order_by("-created_at")[:50].values(
            "action", "resource_type", "ip_address", "created_at"
        )
        data = [
            {
                "action":     l["action"],
                "resource":   l["resource_type"],
                "ip_address": l["ip_address"],
                "created_at": l["created_at"].isoformat() if l["created_at"] else None,
            }
            for l in logs
        ]
        return success_response(data=data, meta={"count": len(data)})
