import pytest
from decimal import Decimal


@pytest.mark.asyncio
async def test_target_funding_rate_for_btc_usd(sdk):
    """Test target funding rate for BTC/USD pair"""
    try:
        target_funding_rate = await sdk.get_target_funding_rate(0)
        print(f"target_funding_rate: {target_funding_rate}")

        assert target_funding_rate == pytest.approx(1, abs=1), \
            f"Failed target_funding_rate assertion for BTC/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_target_funding_rate_for_eth_usd(sdk):
    """Test target funding rate for ETH/USD pair"""
    try:
        target_funding_rate = await sdk.get_target_funding_rate(1)
        print(f"target_funding_rate: {target_funding_rate}")

        assert target_funding_rate == pytest.approx(1, abs=1), \
            f"Failed target_funding_rate assertion for ETH/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")
