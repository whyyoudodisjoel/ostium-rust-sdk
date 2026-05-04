
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig


def main():
    # Example 1: Use testnet configuration
    sdk1 = OstiumSDK(NetworkConfig.testnet())

    # Example 2: Use mainnet configuration
    sdk2 = OstiumSDK(NetworkConfig.mainnet())

    # Example 3: Load from environment variables
    # First, set your environment variables (you'd typically do this in .env file)
    # os.environ['RPC_URL'] = 'https://your-custom-rpc.com'
    # os.environ['OSTIUM_GRAPH_URL'] = 'https://your-custom-graph.com'
    # os.environ['OSTIUM_USDC_ADDRESS'] = '0x123...'
    # os.environ['OSTIUM_TRADING_ADDRESS'] = '0x456...'
    # os.environ['OSTIUM_TRADING_STORAGE_ADDRESS'] = '0x789...'

    # # Then initialize SDK with environment config
    # sdk3 = OstiumSDK(NetworkConfig.from_env())

    # Get block numbers from different configurations
    print(f"Testnet block: {sdk1.w3.eth.block_number}")
    print(f"Mainnet block: {sdk2.w3.eth.block_number}")
    # print(f"Custom env block: {sdk3.w3.eth.block_number}")


if __name__ == "__main__":
    main()
