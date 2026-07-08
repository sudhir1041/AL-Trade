from rest_framework import serializers
from .models import AIScore, MarketRegimeSnapshot


class AIScoreSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="trading_pair.symbol", read_only=True)

    class Meta:
        model  = AIScore
        fields = [
            "id", "symbol", "direction", "confidence_score", "risk_level",
            "market_regime", "entry_zone_low", "entry_zone_high",
            "stop_loss_suggest", "tp1_suggest", "tp2_suggest", "risk_reward_ratio",
            "supporting_factors", "conflicting_factors", "reasoning",
            "mtf_alignment", "compatible_strategies", "is_automated", "created_at",
        ]


class MarketRegimeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MarketRegimeSnapshot
        fields = ["regime", "btc_trend", "eth_trend", "dominance_btc",
                  "fear_greed_index", "factors", "recorded_at"]
