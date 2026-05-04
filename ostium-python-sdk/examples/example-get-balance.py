from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
import asyncio


async def main():
    # Initialize SDK with testnet configuration
    config = NetworkConfig.testnet()
    sdk = OstiumSDK(config)

    # Address to check (replace with the address you want to check)
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    # Get both ETH and USDC balances with forced refresh
    eth_balance, usdc_balance = sdk.balance.get_balance(address, refresh=True)

    print("\nAddress Balances:")
    print("----------------------------------------")
    print(f"Address: {address}")
    print(f"ETH Balance: {eth_balance}")
    print(f"USDC Balance: {usdc_balance}")

if __name__ == "__main__":
    asyncio.run(main())
