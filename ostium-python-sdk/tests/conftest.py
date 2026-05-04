import os
import pytest
from dotenv import load_dotenv
from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig

# Public RPC endpoints for Arbitrum Sepolia
PUBLIC_RPC_URLS = {
    'arbitrum_sepolia': 'https://sepolia-rollup.arbitrum.io/rpc',
    'arbitrum_sepolia_alchemy': 'https://arb-sepolia.g.alchemy.com/v2/demo'
}


@pytest.fixture(scope="session")
def rpc_url():
    """Get RPC URL from environment or use public endpoint"""
    load_dotenv()
    return os.getenv('RPC_URL') or PUBLIC_RPC_URLS['arbitrum_sepolia']


@pytest.fixture(scope="session")
def private_key():
    """Get private key from environment or use test key"""
    load_dotenv()
    return os.getenv('PRIVATE_KEY') or "0x0000000000000000000000000000000000000000000000000000000000000001"


@pytest.fixture(scope="module")
def sdk(rpc_url):
    """Initialize SDK with testnet config"""
    config = NetworkConfig.testnet()
    return OstiumSDK(config, rpc_url=rpc_url)


@pytest.fixture(scope="module")
def mock_sdk():
    """Initialize SDK with mock configuration for unit tests"""
    config = NetworkConfig.testnet()
    return OstiumSDK(config)
