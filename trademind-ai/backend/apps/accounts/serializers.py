"""
apps/accounts/serializers.py
-----------------------------
Authentication serializers: register, login, password management, 2FA.
"""

import pyotp
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from common.utils import generate_secure_token
from .models import (
    AuditLog, EmailVerificationToken, PasswordResetToken,
    TOTPRecoveryCode, User, UserRole,
)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=10, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model  = User
        fields = ["email", "username", "first_name", "last_name", "password", "confirm_password",
                  "timezone", "language", "preferred_currency"]
        extra_kwargs = {"first_name": {"required": False}, "last_name": {"required": False}}

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, data: dict) -> dict:
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(**validated_data)
        # Create email verification token
        token = generate_secure_token(48)
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        # TODO: send verification email via notification service
        return user


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value: str) -> str:
        try:
            record = EmailVerificationToken.objects.select_related("user").get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

        if record.is_used:
            raise serializers.ValidationError("This token has already been used.")
        if record.is_expired:
            raise serializers.ValidationError("This token has expired. Please request a new one.")

        self.context["token_record"] = record
        return value

    def save(self) -> User:
        record: EmailVerificationToken = self.context["token_record"]
        user = record.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        record.is_used = True
        record.save(update_fields=["is_used"])
        return user


# ---------------------------------------------------------------------------
# Custom JWT Login (with 2FA support + device tracking)
# ---------------------------------------------------------------------------

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends simplejwt's default serializer to:
    - Reject inactive accounts
    - Handle 2FA (TOTP OTP code)
    - Embed role + tenant_id in token claims
    """
    totp_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        # Add custom claims
        token["email"]     = user.email
        token["username"]  = user.username
        token["role"]      = user.role
        token["tenant_id"] = str(user.tenant_id) if user.tenant_id else None
        return token

    def validate(self, attrs: dict) -> dict:
        totp_code = attrs.pop("totp_code", "")

        # Authenticate
        credentials = {"email": attrs.get("email"), "password": attrs.get("password")}
        user = authenticate(request=self.context.get("request"), **credentials)

        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid email or password."},
                code="authentication_failed",
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Account not active. Please verify your email."},
                code="account_inactive",
            )

        # 2FA check
        if user.is_2fa_enabled:
            if not totp_code:
                raise serializers.ValidationError(
                    {"totp_code": "Two-factor authentication code is required."},
                    code="2fa_required",
                )
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                raise serializers.ValidationError(
                    {"totp_code": "Invalid two-factor authentication code."},
                    code="2fa_invalid",
                )

        data = super().validate(attrs)

        # Inject user info into response
        data["user"] = {
            "id":       str(user.id),
            "email":    user.email,
            "username": user.username,
            "role":     user.role,
        }
        return data


# ---------------------------------------------------------------------------
# Password Management
# ---------------------------------------------------------------------------

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        # Don't reveal whether email exists (prevent enumeration)
        self.context["email"] = value.lower()
        return value

    def save(self) -> None:
        email = self.context["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
            token = generate_secure_token(48)
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timezone.timedelta(hours=1),
            )
            # TODO: send reset email via notification service
        except User.DoesNotExist:
            pass  # Silently fail to prevent email enumeration


class ResetPasswordSerializer(serializers.Serializer):
    token    = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=10)
    confirm_password = serializers.CharField(write_only=True)

    def validate_token(self, value: str) -> str:
        try:
            record = PasswordResetToken.objects.select_related("user").get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset token.")
        if record.is_used:
            raise serializers.ValidationError("This reset token has already been used.")
        if record.is_expired:
            raise serializers.ValidationError("Reset token has expired. Please request a new one.")
        self.context["token_record"] = record
        return value

    def validate(self, data: dict) -> dict:
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def save(self) -> None:
        record: PasswordResetToken = self.context["token_record"]
        record.user.set_password(self.validated_data["password"])
        record.user.save(update_fields=["password"])
        record.is_used = True
        record.save(update_fields=["is_used"])


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, min_length=10)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data: dict) -> dict:
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if data["current_password"] == data["new_password"]:
            raise serializers.ValidationError({"new_password": "New password must differ from current password."})
        return data

    def save(self) -> None:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])


# ---------------------------------------------------------------------------
# Two-Factor Authentication (TOTP)
# ---------------------------------------------------------------------------

class Enable2FASerializer(serializers.Serializer):
    """Returns a TOTP secret + QR code URI. User must confirm with a valid code."""

    def generate_secret(self, user: User) -> dict:
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save(update_fields=["totp_secret"])
        totp = pyotp.TOTP(secret)
        return {
            "secret":      secret,
            "qr_code_url": totp.provisioning_uri(name=user.email, issuer_name="TradeMind AI"),
        }


class Confirm2FASerializer(serializers.Serializer):
    totp_code = serializers.CharField(max_length=6, min_length=6)

    def validate_totp_code(self, value: str) -> str:
        user = self.context["request"].user
        if not user.totp_secret:
            raise serializers.ValidationError("2FA setup not initiated. Call enable-2fa first.")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(value, valid_window=1):
            raise serializers.ValidationError("Invalid TOTP code.")
        return value

    def save(self) -> list[str]:
        """Enable 2FA and return recovery codes."""
        user = self.context["request"].user
        user.is_2fa_enabled = True
        user.save(update_fields=["is_2fa_enabled"])

        # Delete old recovery codes
        TOTPRecoveryCode.objects.filter(user=user).delete()

        # Generate 10 new recovery codes
        codes = []
        for _ in range(10):
            code = generate_secure_token(8)
            TOTPRecoveryCode.objects.create(user=user, code=code)
            codes.append(code)
        return codes


class Disable2FASerializer(serializers.Serializer):
    password  = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data: dict) -> dict:
        user = self.context["request"].user
        if not user.check_password(data["password"]):
            raise serializers.ValidationError({"password": "Incorrect password."})
        if not user.is_2fa_enabled:
            raise serializers.ValidationError("2FA is not enabled on this account.")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(data["totp_code"], valid_window=1):
            raise serializers.ValidationError({"totp_code": "Invalid TOTP code."})
        return data

    def save(self) -> None:
        user = self.context["request"].user
        user.is_2fa_enabled = False
        user.totp_secret = ""
        user.save(update_fields=["is_2fa_enabled", "totp_secret"])
        TOTPRecoveryCode.objects.filter(user=user).delete()


# ---------------------------------------------------------------------------
# User profile response serializer
# ---------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            "id", "email", "username", "first_name", "last_name", "full_name",
            "role", "is_active", "is_2fa_enabled", "timezone", "language",
            "preferred_currency", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()
