"""
apps/users/models.py
--------------------
User profile, preferences, and API key management for TradeMind AI.

Models
------
- UserProfile     : Extended profile information (1-to-1 with User)
- UserPreferences : Notification & trading preferences (1-to-1 with User)
- UserAPIKey      : Scoped API keys for programmatic platform access
"""

import uuid

from django.db import models

from apps.accounts.models import User


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class UserProfile(models.Model):
    """
    Extended personal information for a user.
    Created automatically when a User is first registered.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="User",
    )
    bio             = models.TextField(blank=True, verbose_name="Bio")
    profile_picture = models.URLField(max_length=512, blank=True, verbose_name="Profile Picture URL")
    phone_number    = models.CharField(max_length=30, blank=True, verbose_name="Phone Number")
    country         = models.CharField(max_length=100, blank=True, verbose_name="Country")
    city            = models.CharField(max_length=100, blank=True, verbose_name="City")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering            = ["user__email"]

    def __str__(self) -> str:
        return f"Profile({self.user.email})"


# ---------------------------------------------------------------------------
# UserPreferences
# ---------------------------------------------------------------------------

class UserPreferences(models.Model):
    """
    Per-user notification channels and trading defaults.
    Created automatically alongside UserProfile.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preferences",
        verbose_name="User",
    )

    # ── Notification channels ───────────────────────────────────────────────
    notification_email    = models.BooleanField(default=True,  verbose_name="Email Notifications")
    notification_telegram = models.BooleanField(default=False, verbose_name="Telegram Notifications")
    notification_push     = models.BooleanField(default=False, verbose_name="Push Notifications")
    notification_discord  = models.BooleanField(default=False, verbose_name="Discord Notifications")
    notification_slack    = models.BooleanField(default=False, verbose_name="Slack Notifications")

    # ── Webhook / chat IDs ──────────────────────────────────────────────────
    telegram_chat_id  = models.CharField(max_length=64,  blank=True, verbose_name="Telegram Chat ID")
    discord_webhook   = models.URLField(max_length=512,  blank=True, verbose_name="Discord Webhook URL")
    slack_webhook     = models.URLField(max_length=512,  blank=True, verbose_name="Slack Webhook URL")

    # ── Trading defaults ────────────────────────────────────────────────────
    default_risk_profile  = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Default Risk Profile",
        help_text="Name or type key of the user's default RiskProfile.",
    )
    default_strategy_id   = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Default Strategy ID",
        help_text="UUID of the user's preferred strategy.",
    )
    auto_trading_enabled  = models.BooleanField(default=False, verbose_name="Auto-Trading Enabled")
    paper_trading_mode    = models.BooleanField(default=False, verbose_name="Paper-Trading Mode")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "User Preferences"
        verbose_name_plural = "User Preferences"
        ordering            = ["user__email"]

    def __str__(self) -> str:
        return f"Preferences({self.user.email})"


# ---------------------------------------------------------------------------
# UserAPIKey
# ---------------------------------------------------------------------------

class UserAPIKey(models.Model):
    """
    Scoped API key for programmatic access to the TradeMind platform.

    The raw key is shown only once at creation time.
    key_hash  stores the bcrypt/SHA-256 hash of the full key.
    key_prefix stores the first 8 characters for safe display in the UI.
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="User",
    )
    name        = models.CharField(max_length=255, verbose_name="Key Name")
    # Never store the raw key
    key_hash    = models.CharField(max_length=256, verbose_name="Key Hash (hashed)")
    key_prefix  = models.CharField(
        max_length=8,
        verbose_name="Key Prefix",
        help_text="First 8 characters of the raw key; safe to display in the UI.",
    )
    permissions = models.JSONField(
        default=list,
        verbose_name="Permissions",
        help_text="List of permission scopes granted to this key, e.g. ['read:portfolio', 'write:orders'].",
    )
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name="Last Used At")
    expires_at   = models.DateTimeField(null=True, blank=True, verbose_name="Expires At")
    is_active    = models.BooleanField(default=True, verbose_name="Active")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "User API Key"
        verbose_name_plural = "User API Keys"
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["key_prefix"]),
        ]

    def __str__(self) -> str:
        return f"APIKey({self.key_prefix}…, user={self.user_id}, name='{self.name}')"
