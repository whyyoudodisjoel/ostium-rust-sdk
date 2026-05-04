from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
import asyncio


async def main():
    # Initialize with testnet config
    config = NetworkConfig.testnet()
    # Or for mainnet:
    # config = NetworkConfig.mainnet()

    sdk = OstiumSDK(config)

    # Example address - replace with the address you want to query
    address = "0x3750A14869d419F1069cbF7cbE47A89b2Dc1d4c4"

    # Fetch all positions for the address using the subgraph client
    positions = await sdk.subgraph.get_open_trades(address)

    # Print positions information
    print(f"\nPositions for address: {address}")
    print("----------------------------------------")

    if not positions:
        print("No open positions found")
        return

    for position in positions:
        print(f"Trade ID: {position['tradeID']}")
        print(f"Pair Index: {position['index']}")
        print(f"Market: {position['pair']['from']}/{position['pair']['to']}")
        print(f"Direction: {'Long' if position['isBuy'] else 'Short'}")
        print(f"Leverage: {int(position['leverage'])/100}x")
        print(f"Collateral: {float(position['collateral'])/1e6} USDC")
        print(f"Open Price: ${float(position['openPrice'])/1e18:,.2f}")
        if position['takeProfitPrice'] != "0":
            print(
                f"Take Profit: ${float(position['takeProfitPrice'])/1e18:,.2f}")
        if position['stopLossPrice'] != "0":
            print(f"Stop Loss: ${float(position['stopLossPrice'])/1e18:,.2f}")
        print(f"Notional: {float(position['notional'])/1e6} USDC")
        print(f"Funding: {float(position['funding'])/1e18:,.8f}")
        print("----------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
