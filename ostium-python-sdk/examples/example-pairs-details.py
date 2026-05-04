from ostium_python_sdk import OstiumSDK, NetworkConfig
from dotenv import load_dotenv
import os
import asyncio


async def main():
    # Load environment variables if using .env file
    load_dotenv()

    # Get private key from environment variable
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("PRIVATE_KEY not found in .env file")

    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        raise ValueError("RPC_URL not found in .env file")

    # Initialize SDK
    config = NetworkConfig.testnet()
    sdk = OstiumSDK(config, private_key)

    try:
        # Get formatted pairs details
        formatted_pairs = await sdk.get_formatted_pairs_details()

        print("\nFormatted Pair Information:")
        print("----------------------------------------")

        for pair in formatted_pairs:
            print("\nFormatted Pair Details:")
            print("----------------------------------------")
            # Print all available fields in formatted pair details
            for key, value in pair.items():
                print(f"{key}: {value}")
            print("----------------------------------------")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
