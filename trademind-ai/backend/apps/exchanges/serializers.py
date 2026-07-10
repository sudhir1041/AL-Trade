"""
apps/exchanges/serializers.py
------------------------------
Exchange integration serializers — accounts, API key management, balances.
"""

from rest_framework import serializers

from common.utils import mask_secret

from .models import Exchange, ExchangeAccount, ExchangeConnection, ExchangeLog


class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
            "is_active",
            "supports_futures",
            "supports_spot",
            "supports_websocket",
            "sandbox_available",
            "phase",
        ]


class ExchangeAccountCreateSerializer(serializers.ModelSerializer):
    """Used for creating a new exchange account — accepts raw credentials."""

    api_key = serializers.CharField(write_only=True)
    api_secret = serializers.CharField(write_only=True)
    api_passphrase = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = ExchangeAccount
        fields = [
            "exchange",
            "label",
            "api_key",
            "api_secret",
            "api_passphrase",
            "is_testnet",
        ]

    def create(self, validated_data: dict) -> ExchangeAccount:
        from django.conf import settings

        from common.utils import encrypt_secret

        key = validated_data.pop("api_key")
        secret = validated_data.pop("api_secret")
        passphrase = validated_data.pop("api_passphrase", "")
        enc_key = settings.FIELD_ENCRYPTION_KEY

        return ExchangeAccount.objects.create(
            **validated_data,
            api_key_encrypted=encrypt_secret(key, enc_key),
            api_secret_encrypted=encrypt_secret(secret, enc_key),
            api_passphrase_encrypted=(
                encrypt_secret(passphrase, enc_key) if passphrase else ""
            ),
        )


class ExchangeAccountSerializer(serializers.ModelSerializer):
    """Read-only representation — never exposes raw secrets."""

    exchange_name = serializers.CharField(source="exchange.name", read_only=True)
    exchange_slug = serializers.CharField(source="exchange.slug", read_only=True)
    exchange_logo = serializers.CharField(source="exchange.logo_url", read_only=True)
    api_key_masked = serializers.SerializerMethodField()

    class Meta:
        model = ExchangeAccount
        fields = [
            "id",
            "exchange",
            "exchange_name",
            "exchange_slug",
            "exchange_logo",
            "label",
            "api_key_masked",
            "is_active",
            "is_testnet",
            "connection_status",
            "last_sync_at",
            "balance_synced_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_api_key_masked(self, obj: ExchangeAccount) -> str:
        """Return only the last 4 chars of the encrypted key prefix."""
        return mask_secret(
            obj.api_key_encrypted[:12] if obj.api_key_encrypted else "", 4
        )


class ExchangeAccountUpdateSerializer(serializers.ModelSerializer):
    """PATCH — update label or testnet flag only (not credentials)."""

    class Meta:
        model = ExchangeAccount
        fields = ["label", "is_active", "is_testnet"]


class ExchangeConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeConnection
        fields = ["id", "status", "connected_at", "disconnected_at", "error_message"]


class ExchangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeLog
        fields = [
            "id",
            "action",
            "status_code",
            "latency_ms",
            "error_message",
            "created_at",
        ]
