"""
apps/accounts/views.py
----------------------
Authentication API views: register, login, logout, 2FA, password management.
"""

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.responses import (
    created_response, error_response, no_content_response,
    success_response, unauthorized_response,
)
from .models import RefreshTokenRecord, UserDevice
from .serializers import (
    ChangePasswordSerializer,
    Confirm2FASerializer,
    Disable2FASerializer,
    Enable2FASerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    CustomTokenObtainPairSerializer,
)

logger = logging.getLogger("trademind.accounts")


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class RegisterView(APIView):
    """
    POST /auth/register
    Create a new user account. Account is inactive until email is verified.
    """
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Registration failed.",
                details={"field_errors": serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        logger.info("New user registered: %s", user.email)
        return created_response(
            data={"user_id": str(user.id), "email": user.email},
            message="Registration successful. Please check your email to verify your account.",
        )


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

class VerifyEmailView(APIView):
    """POST /auth/verify-email"""
    permission_classes = [AllowAny]

    def post(self, request: Request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Email verification failed.",
                                   details=serializer.errors)
        user = serializer.save()
        logger.info("Email verified for user: %s", user.email)
        return success_response(
            data={"email": user.email},
            message="Email verified successfully. You can now log in.",
        )


# ---------------------------------------------------------------------------
# Login (JWT)
# ---------------------------------------------------------------------------

class LoginView(TokenObtainPairView):
    """
    POST /auth/login
    Returns access_token + refresh_token + user info.
    Handles 2FA if enabled.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = "auth"

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            return error_response(
                "AUTHENTICATION_FAILED",
                str(exc.detail) if hasattr(exc, "detail") else "Authentication failed.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data

        # Track device
        user_id = data.get("user", {}).get("id")
        if user_id:
            self._register_device(request, user_id)

        logger.info("User logged in: %s", data.get("user", {}).get("email"))
        return success_response(
            data={
                "access_token":  data["access"],
                "refresh_token": data["refresh"],
                "token_type":    "Bearer",
                "user":          data.get("user", {}),
            },
            message="Login successful.",
        )

    def _register_device(self, request: Request, user_id: str) -> None:
        try:
            UserDevice.objects.update_or_create(
                user_id=user_id,
                device_id=request.META.get("HTTP_X_DEVICE_ID", ""),
                defaults={
                    "device_name": request.META.get("HTTP_X_DEVICE_NAME", "Unknown"),
                    "device_type": request.META.get("HTTP_X_DEVICE_TYPE", "web"),
                    "last_ip":     request.META.get("REMOTE_ADDR"),
                    "last_seen":   timezone.now(),
                },
            )
        except Exception:
            pass  # Non-critical; don't fail login on device tracking error


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutView(APIView):
    """
    POST /auth/logout
    Blacklists the provided refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return error_response("VALIDATION_ERROR", "refresh_token is required.")

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return error_response("TOKEN_ERROR", str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        logger.info("User logged out: %s", request.user.email)
        return success_response(message="Logged out successfully.")


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------

class TokenRefreshView(APIView):
    """POST /auth/refresh"""
    permission_classes = [AllowAny]

    def post(self, request: Request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return error_response("VALIDATION_ERROR", "refresh_token is required.")

        try:
            token = RefreshToken(refresh_token)
            return success_response(
                data={"access_token": str(token.access_token)},
                message="Token refreshed.",
            )
        except TokenError as exc:
            return unauthorized_response(str(exc))


# ---------------------------------------------------------------------------
# Password Management
# ---------------------------------------------------------------------------

class ForgotPasswordView(APIView):
    """POST /auth/forgot-password"""
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request: Request):
        serializer = ForgotPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Always return 200 regardless (prevent email enumeration)
        return success_response(
            message="If an account with that email exists, a password reset link has been sent."
        )


class ResetPasswordView(APIView):
    """POST /auth/reset-password"""
    permission_classes = [AllowAny]

    def post(self, request: Request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Password reset failed.", details=serializer.errors)
        serializer.save()
        return success_response(message="Password reset successfully. You can now log in.")


class ChangePasswordView(APIView):
    """POST /auth/change-password"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Password change failed.", details=serializer.errors)
        serializer.save()
        logger.info("Password changed for user: %s", request.user.email)
        return success_response(message="Password changed successfully.")


# ---------------------------------------------------------------------------
# Two-Factor Authentication
# ---------------------------------------------------------------------------

class Enable2FAView(APIView):
    """POST /auth/enable-2fa — initiates 2FA setup, returns QR code URI."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = Enable2FASerializer()
        result = serializer.generate_secret(request.user)
        return success_response(
            data=result,
            message="Scan the QR code with your authenticator app, then confirm with a TOTP code.",
        )


class Confirm2FAView(APIView):
    """POST /auth/confirm-2fa — verifies TOTP and activates 2FA."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = Confirm2FASerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "2FA confirmation failed.", details=serializer.errors)
        recovery_codes = serializer.save()
        logger.info("2FA enabled for user: %s", request.user.email)
        return success_response(
            data={"recovery_codes": recovery_codes},
            message="2FA enabled successfully. Store your recovery codes safely.",
        )


class Disable2FAView(APIView):
    """POST /auth/disable-2fa"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = Disable2FASerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "2FA disabling failed.", details=serializer.errors)
        serializer.save()
        logger.info("2FA disabled for user: %s", request.user.email)
        return success_response(message="2FA disabled successfully.")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileView(APIView):
    """GET /auth/profile | PATCH /auth/profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        return success_response(
            data=UserSerializer(request.user).data,
            message="Profile retrieved.",
        )

    def patch(self, request: Request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Profile update failed.", details=serializer.errors)
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated.")


# ---------------------------------------------------------------------------
# Account Deletion
# ---------------------------------------------------------------------------

class DeleteAccountView(APIView):
    """DELETE /auth/account"""
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request):
        user = request.user
        # Soft-delete: deactivate account
        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info("Account deactivated: %s", user.email)
        return success_response(
            message="Account deactivated. Contact support to restore it within 30 days."
        )
