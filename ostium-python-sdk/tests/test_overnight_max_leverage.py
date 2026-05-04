import pytest
from decimal import Decimal


@pytest.mark.asyncio
async def test_overnight_max_leverage_validation_for_btc_usd(sdk):
    """Test overnight max leverage for BTC/USD pair"""
    try:
        overnight_max_leverage = await sdk.get_pair_overnight_max_leverage(0)
        print(f"overnight_max_leverage: {overnight_max_leverage}")

        assert overnight_max_leverage == pytest.approx(None, abs=1e-5), \
            f"Failed get_pair_overnight_max_leverage assertion for BTC/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_overnight_max_leverage_validation_for_eth_usd(sdk):
    """Test overnight max leverage for ETH/USD pair"""
    try:
        overnight_max_leverage = await sdk.get_pair_overnight_max_leverage(1)
        print(f"overnight_max_leverage: {overnight_max_leverage}")

        assert overnight_max_leverage == pytest.approx(None, abs=1e-5), \
            f"Failed get_pair_overnight_max_leverage assertion for ETH/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_overnight_max_leverage_validation_for_tsla_usd(sdk):
    """Test overnight max leverage for TSLA/USD pair"""
    try:
        overnight_max_leverage = await sdk.get_pair_overnight_max_leverage(22)
        print(f"overnight_max_leverage: {overnight_max_leverage}")

        assert overnight_max_leverage == pytest.approx(10, abs=1e-5), \
            f"Failed get_pair_overnight_max_leverage assertion for TSLA/USD"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")
