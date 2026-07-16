"""
apps/market/serializers.py
--------------------------
Market data serializers — tickers, OHLCV, order book, funding rates.
"""

from rest_framework import serializers
from .models import TradingPair, Ticker, OHLCV, FundingRate, OpenInterest, Liquidation


class TradingPairSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source="exchange.name", read_only=True)

    class Meta:
        model  = TradingPair
        fields = [
            "id", "exchange", "exchange_name", "symbol",
            "base_asset", "quote_asset", "is_active", "is_futures",
            "min_quantity", "price_step", "quantity_step",
        ]


class TickerSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="trading_pair.symbol", read_only=True)

    class Meta:
        model  = Ticker
        fields = [
            "symbol", "price", "bid", "ask",
            "high_24h", "low_24h", "volume_24h",
            "change_24h_pct", "timestamp",
        ]


class OHLCVSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OHLCV
        fields = ["timeframe", "open", "high", "low", "close", "volume", "timestamp"]


class FundingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FundingRate
        fields = ["rate", "next_funding_time", "timestamp"]


class OpenInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OpenInterest
        fields = ["open_interest", "timestamp"]
