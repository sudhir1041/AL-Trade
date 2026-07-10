import pytest

from apps.exchanges.adapters.binance import BinanceAdapter


def test_binance_adapter_init():
    adapter = BinanceAdapter(api_secret="test", is_testnet=True)
    assert adapter.exchange_slug == "binance"
    assert adapter.exchange_name == "Binance"
    assert adapter.api_secret == "test"
    assert adapter.is_testnet is True


@pytest.mark.asyncio
async def test_binance_ping():
    adapter = BinanceAdapter(api_secret="test", is_testnet=True)
    result = await adapter.ping()
    assert result is True


@pytest.mark.asyncio
async def test_binance_connect():
    adapter = BinanceAdapter(api_secret="test")
    assert adapter.is_connected is False
    await adapter.connect()
    assert adapter.is_connected is True
    await adapter.disconnect()
    assert adapter.is_connected is False
