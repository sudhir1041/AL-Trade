"""
apps/accounts/models.py
-----------------------
Authentication & identity models for TradeMind AI.

Models
------
- User               : Custom AUTH_USER_MODEL
- EmailVerificationToken
- PasswordResetToken
- RefreshTokenRecord
- UserDevice
- TOTPRecoveryCode
- AuditLog
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class UserRole(models.TextChoices):
    GUEST        = "GUEST",        "Guest"
    USER         = "USER",         "User"
    PREMIUM      = "PREMIUM",      "Premium"
    ENTERPRISE   = "ENTERPRISE",   "Enterprise"
    SUPPORT      = "SUPPORT",      "Support"
    ADMIN        = "ADMIN",        "Admin"
    SUPER_ADMIN  = "SUPER_ADMIN",  "Super Admin"


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class UserManager(BaseUserManager):
    """Custom manager for the User model using email as the unique identifier."""

    def _create_user(self, email: str, username: str, password: str, **extra):
        if not email:
            raise ValueError("An email address is required.")
        if not username:
            raise ValueError("A username is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, username: str, password: str = None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra)

    def create_superuser(self, email: str, username: str, password: str, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("role", UserRole.SUPER_ADMIN)
        return self._create_user(email, username, password, **extra)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.  Email is the login credential.
    Accounts are inactive until the user completes email verification.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    tenant_id = models.UUIDField(
        db_index=True,
        null=True,
        blank=True,
        help_text="UUID of the tenant this user belongs to (null for platform admins).",
    )

    # ── Credentials ────────────────────────────────────────────────────────
    email    = models.EmailField(unique=True, verbose_name="Email Address")
    username = models.CharField(max_length=150, unique=True, verbose_name="Username")

    # ── Name ───────────────────────────────────────────────────────────────
    first_name = models.CharField(max_length=150, blank=True, verbose_name="First Name")
    last_name  = models.CharField(max_length=150, blank=True, verbose_name="Last Name")

    # ── Status flags ───────────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=False,
        help_text="Activated after email verification.",
    )
    is_staff = models.BooleanField(default=False)

    # ── Timestamps ─────────────────────────────────────────────────────────
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date Joined")
    updated_at  = models.DateTimeField(auto_now=True,     verbose_name="Updated At")

    # ── Role ───────────────────────────────────────────────────────────────
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name="Role",
    )

    # ── Two-factor authentication ───────────────────────────────────────────
    totp_secret    = models.CharField(max_length=64, blank=True, verbose_name="TOTP Secret")
    is_2fa_enabled = models.BooleanField(default=False, verbose_name="2FA Enabled")

    # ── Localisation / preferences ─────────────────────────────────────────
    timezone           = models.CharField(max_length=50,  default="UTC",  verbose_name="Timezone")
    language           = models.CharField(max_length=10,  default="en",   verbose_name="Language")
    preferred_currency = models.CharField(max_length=10,  default="USDT", verbose_name="Preferred Currency")

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        verbose_name        = "User"
        verbose_name_plural = "Users"
        ordering            = ["-date_joined"]
        indexes = [
            models.Index(fields=["tenant_id"]),
            models.Index(fields=["role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_full_name() or self.username})"

    # ── Helpers ────────────────────────────────────────────────────────────
    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.username


# ---------------------------------------------------------------------------
# Email Verification Token
# ---------------------------------------------------------------------------

class EmailVerificationToken(models.Model):
    """One-time token sent to the user's email to activate their account."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token      = models.CharField(max_length=256, unique=True, verbose_name="Token")
    expires_at = models.DateTimeField(verbose_name="Expires At")
    is_used    = models.BooleanField(default=False, verbose_name="Used")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self) -> str:
        return f"EmailVerificationToken(user={self.user_id}, used={self.is_used})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


# ---------------------------------------------------------------------------
# Password Reset Token
# ---------------------------------------------------------------------------

class PasswordResetToken(models.Model):
    """One-time token used to reset a user's password."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token      = models.CharField(max_length=256, unique=True, verbose_name="Token")
    expires_at = models.DateTimeField(verbose_name="Expires At")
    is_used    = models.BooleanField(default=False, verbose_name="Used")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self) -> str:
        return f"PasswordResetToken(user={self.user_id}, used={self.is_used})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


# ---------------------------------------------------------------------------
# Refresh Token Record
# ---------------------------------------------------------------------------

class RefreshTokenRecord(models.Model):
    """
    Persisted record of each issued JWT refresh token (identified by its JTI).
    Allows selective revocation without a full token blacklist scan.
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="refresh_token_records",
    )
    # JWT ID claim — unique per issued token
    jti         = models.CharField(max_length=128, unique=True, verbose_name="JTI")
    expires_at  = models.DateTimeField(verbose_name="Expires At")
    revoked_at  = models.DateTimeField(null=True, blank=True, verbose_name="Revoked At")
    device_info = models.JSONField(
        default=dict,
        verbose_name="Device Info",
        help_text="Metadata about the device/browser that requested the token.",
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Refresh Token Record"
        verbose_name_plural = "Refresh Token Records"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["jti"]),
            models.Index(fields=["user", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"RefreshToken(user={self.user_id}, jti={self.jti[:12]}…)"

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


# ---------------------------------------------------------------------------
# User Device
# ---------------------------------------------------------------------------

class UserDevice(models.Model):
    """Tracks devices used to log into the platform."""

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    device_id   = models.UUIDField(default=uuid.uuid4, verbose_name="Device ID")
    device_name = models.CharField(max_length=255, blank=True, verbose_name="Device Name")
    device_type = models.CharField(max_length=100, blank=True, verbose_name="Device Type")
    last_ip     = models.GenericIPAddressField(null=True, blank=True, verbose_name="Last IP")
    last_seen   = models.DateTimeField(null=True, blank=True, verbose_name="Last Seen")
    is_trusted  = models.BooleanField(default=False, verbose_name="Trusted")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "User Device"
        verbose_name_plural = "User Devices"
        ordering            = ["-last_seen"]
        indexes = [
            models.Index(fields=["user", "device_id"]),
            models.Index(fields=["user", "is_trusted"]),
        ]

    def __str__(self) -> str:
        return f"{self.device_name or self.device_type} – {self.user_id}"


# ---------------------------------------------------------------------------
# TOTP Recovery Code
# ---------------------------------------------------------------------------

class TOTPRecoveryCode(models.Model):
    """
    Single-use backup code for TOTP 2FA recovery.
    Codes are stored hashed; comparison must be done in the service layer.
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="totp_recovery_codes",
    )
    # Store the hashed code, never the plaintext
    code       = models.CharField(max_length=128, verbose_name="Hashed Code")
    is_used    = models.BooleanField(default=False, verbose_name="Used")
    created_at = models.DateTimeField(auto_now_add=True)
    used_at    = models.DateTimeField(null=True, blank=True, verbose_name="Used At")

    class Meta:
        verbose_name        = "TOTP Recovery Code"
        verbose_name_plural = "TOTP Recovery Codes"
        ordering            = ["created_at"]
        indexes = [
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self) -> str:
        return f"TOTPRecoveryCode(user={self.user_id}, used={self.is_used})"


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLog(models.Model):
    """
    Immutable audit trail for all significant platform events.
    Rows are append-only; never update or delete them.
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # user is nullable to allow system-generated events
    user          = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    tenant_id     = models.UUIDField(db_index=True, verbose_name="Tenant ID")
    action        = models.CharField(max_length=128, db_index=True, verbose_name="Action")
    resource_type = models.CharField(max_length=128, verbose_name="Resource Type")
    resource_id   = models.CharField(max_length=128, blank=True, verbose_name="Resource ID")
    ip_address    = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent    = models.TextField(blank=True, verbose_name="User Agent")
    old_value     = models.JSONField(null=True, blank=True, verbose_name="Old Value")
    new_value     = models.JSONField(null=True, blank=True, verbose_name="New Value")
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "action"]),
            models.Index(fields=["tenant_id", "resource_type", "resource_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"AuditLog({self.action} on {self.resource_type}/{self.resource_id})"
