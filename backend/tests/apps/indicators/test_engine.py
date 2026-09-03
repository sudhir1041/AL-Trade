import pytest
import pandas as pd
import numpy as np
import math
from decimal import Decimal
from apps.indicators.engine import IndicatorEngine

# Dummy class to avoid django dependency setup issues if the engine requires a real model instance
class DummyEngine(IndicatorEngine):
    def __init__(self):
        pass

@pytest.fixture
def sample_df():
    # 200 rows of deterministic sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
    # Generate prices that fluctuate to ensure losses and gains
    close = np.linspace(100, 150, 250) + np.sin(np.linspace(0, 50, 250)) * 20
    high = close + 2
    low = close - 2
    volume = np.random.randint(1000, 5000, size=250)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': close - 1,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    return df

def test_sma_calculation(sample_df):
    engine = DummyEngine()
    result = engine._sma(sample_df)

    assert "sma_20" in result
    assert "sma_50" in result
    assert "sma_200" in result

    # Check that they are float and calculate properly
    expected_sma_20 = round(float(sample_df["close"].rolling(20).mean().iloc[-1]), 6)
    assert result["sma_20"] == expected_sma_20

def test_rsi_calculation(sample_df):
    engine = DummyEngine()
    result = engine._rsi(sample_df)

    assert "rsi" in result
    assert "rsi_oversold" in result
    assert "rsi_overbought" in result

    # RSI must be between 0 and 100
    assert not math.isnan(result["rsi"])
    assert 0 <= result["rsi"] <= 100

def test_macd_calculation(sample_df):
    engine = DummyEngine()
    result = engine._macd(sample_df)

    assert "macd" in result
    assert "macd_signal" in result
    assert "macd_histogram" in result
    assert "macd_bullish" in result

    # Check that macd - signal = histogram
    assert abs((result["macd"] - result["macd_signal"]) - result["macd_histogram"]) < 1e-4
