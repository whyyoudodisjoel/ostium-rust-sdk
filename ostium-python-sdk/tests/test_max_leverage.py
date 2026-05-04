import pytest
from decimal import Decimal


@pytest.mark.asyncio
async def test_max_leverage_validation_for_btc_usd(sdk):
    """Test max leverage for BTC/USD pair"""
    try:
        max_leverage = await sdk.get_pair_max_leverage(0)
        print(f"max_leverage: {max_leverage}")

        assert max_leverage == pytest.approx(50, abs=1e-5), \
            f"Failed get_pair_max_leverage assertion for BTC/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_max_leverage_validation_for_eth_usd(sdk):
    """Test max leverage for ETH/USD pair"""
    try:
        max_leverage = await sdk.get_pair_max_leverage(1)
        print(f"max_leverage: {max_leverage}")

        assert max_leverage == pytest.approx(50, abs=1e-5), \
            f"Failed get_pair_max_leverage assertion for ETH/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_max_leverage_validation_for_ftse_usd(sdk):
    """Test max leverage for FTSE/USD pair"""
    try:
        max_leverage = await sdk.get_pair_max_leverage(14)
        print(f"max_leverage: {max_leverage}")

        assert max_leverage == pytest.approx(100, abs=1e-5), \
            f"Failed get_pair_max_leverage assertion for FTSE/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_max_leverage_validation_for_tsla_usd(sdk):
    """Test max leverage for TSLA/USD pair"""
    try:
        max_leverage = await sdk.get_pair_max_leverage(22)
        print(f"max_leverage: {max_leverage}")

        assert max_leverage == pytest.approx(100, abs=1e-5), \
            f"Failed get_pair_max_leverage assertion for TSLA/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")
