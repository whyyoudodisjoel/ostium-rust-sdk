import os
import asyncio
from decimal import Decimal
import pytest
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
from eth_account import Account


@pytest.fixture(scope="module")
def sdk():
    # Load environment variables
    load_dotenv()

    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        raise ValueError("RPC_URL not found in .env file")

    # Initialize SDK with testnet config
    config = NetworkConfig.testnet()
    return OstiumSDK(config)


@pytest.mark.asyncio
async def test_slippage_validation(sdk):
    # Get address from private key
    if not os.getenv('PRIVATE_KEY'):
        pytest.skip(
            "PRIVATE_KEY not found in .env file (test requires private key)")

    account = Account.from_key(os.getenv('PRIVATE_KEY'))

    # Check ETH and USDC balances first
    eth_balance, usdc_balance = sdk.balance.get_balance(account.address)
    print(f"Current ETH balance: {eth_balance}")
    print(f"Current USDC balance: {usdc_balance}")

    if eth_balance < Decimal('0.001'):
        msg = f"Insufficient ETH balance: {eth_balance} ETH (need at least 0.05 ETH for gas)"
        pytest.skip(msg)

    if usdc_balance < Decimal('100'):
        msg = f"Insufficient USDC balance: {usdc_balance} USDC (need at least 100 USDC)"
        pytest.skip(msg)

    # Get latest price for BTC
    latest_price, _, _ = await sdk.price.get_price("BTC", "USD")
    latest_price = Decimal(str(latest_price))  # Convert float to Decimal
    print(f"Latest price: {latest_price}")

    # Define base trade parameters
    trade_params = {
        'collateral': Decimal('100'),
        'leverage': Decimal('30'),
        'asset_type': 0,          # BTC-USD
        'direction': True,        # Long
        'order_type': 'MARKET'
    }
    MAX_SLIPPAGE_PERCENTAGE = 1
    # Test case 1: Trade within slippage should succeed
    sdk.ostium.set_slippage_percentage(MAX_SLIPPAGE_PERCENTAGE)

    print(
        f"Slippage percentage set to: {sdk.ostium.get_slippage_percentage()}%")

    try:
        receipt = sdk.ostium.perform_trade(trade_params, at_price=latest_price)
        assert receipt is not None
        print("Trade at exact price succeeded")
    except Exception as e:
        pytest.fail(f"Trade at exact price should not fail: {str(e)}")

    # Test case 2: Trade with price outside slippage range (should fail)
    await asyncio.sleep(1)  # Wait a bit to ensure price feed has updated

    price_higher_than_latest = 1+((MAX_SLIPPAGE_PERCENTAGE+2)/100)

    price_outside_range = latest_price * \
        Decimal(price_higher_than_latest)  # X% higher than latest price
    print(
        f"Attempting trade at price {price_outside_range} ({price_higher_than_latest}x higher than {latest_price}, while slippage is {MAX_SLIPPAGE_PERCENTAGE}%)")

    try:
        receipt = sdk.ostium.perform_trade(
            trade_params, at_price=price_outside_range)

        print("Placing market order...")
        trade_result = sdk.ostium.perform_trade(
            trade_params, at_price=latest_price)

        # Get transaction receipt and order ID
        receipt = trade_result['receipt']
        order_id = trade_result['order_id']

        print(f"Order placed!")
        print(f"Transaction hash: {receipt['transactionHash'].hex()}")
        print(f"Order ID: {order_id}")

        # Track the order until it's processed and get the resulting trade
        print("\nTracking order status...")
        result = await sdk.ostium.track_order_and_trade(sdk.subgraph, order_id)

        if result['order']:
            pytest.fail(
                "Trade should have failed due to slippage, but succeeded")

    except Exception as e:
        assert "execution reverted" in str(e)
        print("Trade outside slippage range correctly failed")
