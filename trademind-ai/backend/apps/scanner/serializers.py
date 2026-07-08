"""
apps/scanner/serializers.py
T5 ✅
"""
from rest_framework import serializers
from .models import ScannerJob, ScannerResult, ScannerSettings


class ScannerJobSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ScannerJob
        fields = [
            "id", "status", "started_at", "completed_at",
            "pairs_scanned", "candidates_found", "rejected_count",
            "duration_ms", "error_message", "created_at",
        ]


class ScannerResultSerializer(serializers.ModelSerializer):
    symbol        = serializers.CharField(source="trading_pair.symbol",       read_only=True)
    exchange_name = serializers.CharField(source="trading_pair.exchange.name", read_only=True)

    class Meta:
        model  = ScannerResult
        fields = [
            "id", "symbol", "exchange_name",
            "confidence_score", "risk_score", "trend_direction",
            "volume_24h_usdt", "volume_spike", "spread_pct",
            "btc_correlation", "eth_correlation",
            "factors", "is_candidate", "rejection_reason", "created_at",
        ]


class ScannerSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ScannerSettings
        fields = [
            "min_volume_usdt", "min_liquidity_score", "max_spread_pct",
            "volatility_min", "volatility_max",
            "require_trend", "require_volume_spike",
            "min_rsi", "max_rsi", "min_confidence_score",
            "scan_interval_seconds", "is_active", "enabled_exchanges",
        ]
