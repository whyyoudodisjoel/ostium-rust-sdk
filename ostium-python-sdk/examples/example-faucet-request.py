import os
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
from eth_account import Account
import asyncio
from datetime import datetime

print("Debug - Starting example script")


async def main():
    # Load environment variables from .env file
    load_dotenv()
    print("Debug - Loaded env vars")

    # Get private key and RPC URL from environment variables
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("PRIVATE_KEY not found in .env file")

    rpc_url = os.getenv('RPC_URL')
    if not rpc_url:
        raise ValueError("RPC_URL not found in .env file")

    print("Debug - Got private key and RPC URL")

    # Get account address from private key
    account = Account.from_key(private_key)
    address = account.address

    print("\n=== Testnet Faucet Example ===")

    # Initialize SDK with testnet config and RPC URL
    config = NetworkConfig.testnet()
    print("Debug - Created NetworkConfig")

    sdk = OstiumSDK(config, private_key)
    print("Debug - Created SDK")

    try:
        # Check if tokens can be requested
        if sdk.faucet.can_request_tokens(address):
            # Get amount that will be received
            amount = sdk.faucet.get_token_amount()
            # Convert from wei to USDC
            print(f"Will receive {amount/1e6} USDC")

            # Request tokens
            receipt = sdk.faucet.request_tokens()
            print(f"Tokens requested successfully!")
            print(f"Transaction hash: {receipt['transactionHash'].hex()}")
        else:
            next_time = sdk.faucet.get_next_request_time(address)
            next_time_str = datetime.fromtimestamp(
                next_time).strftime('%Y-%m-%d %H:%M:%S')
            print(
                f"Cannot request tokens yet. Next request allowed at: {next_time_str}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
