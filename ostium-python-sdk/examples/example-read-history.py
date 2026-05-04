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

    # Fetch all history for the address using the subgraph client
    history = await sdk.subgraph.get_recent_history(address, 10)

    # Print history information
    print(f"\nHistory for address: {address}")
    print("----------------------------------------")

    if not history:
        print("No history found")
        return

    for history_record in history:
        print(history_record)
        print("----------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
