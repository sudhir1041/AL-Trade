"""
apps/users/serializers.py
T2.3 ✅
"""
from rest_framework import serializers
from .models import UserProfile, UserPreferences, UserAPIKey
from apps.accounts.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserProfile
        fields = ["bio", "profile_picture", "phone_number", "country", "city"]


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserPreferences
        fields = [
            "notification_email", "notification_telegram", "notification_push",
            "notification_discord", "notification_slack",
            "telegram_chat_id", "discord_webhook", "slack_webhook",
            "default_risk_profile", "auto_trading_enabled", "paper_trading_mode",
        ]


class UserMeSerializer(serializers.ModelSerializer):
    profile     = UserProfileSerializer(source="userprofile",     read_only=True)
    preferences = UserPreferencesSerializer(source="userpreferences", read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "role", "timezone", "language", "preferred_currency",
            "is_2fa_enabled", "date_joined",
            "profile", "preferences",
        ]
        read_only_fields = ["id", "email", "role", "date_joined"]


class UserAPIKeySerializer(serializers.ModelSerializer):
    key_display = serializers.SerializerMethodField()

    class Meta:
        model  = UserAPIKey
        fields = ["id", "name", "key_display", "permissions",
                  "last_used_at", "expires_at", "is_active", "created_at"]

    def get_key_display(self, obj):
        return f"{obj.key_prefix}{'*' * 24}"


class UserActivitySerializer(serializers.Serializer):
    action      = serializers.CharField()
    resource    = serializers.CharField()
    ip_address  = serializers.IPAddressField(allow_null=True)
    created_at  = serializers.DateTimeField()
