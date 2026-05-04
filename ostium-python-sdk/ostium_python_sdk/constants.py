
# Constants
from decimal import Decimal

CHAIN_ID_ARBITRUM_MAINNET = 42161   # Arbitrum One
CHAIN_ID_ARBITRUM_TESTNET = 421614  # Arbitrum Sepolia

MAX_PROFIT_P = Decimal('900')  # 900% * PRECISION_6
MAX_STOP_LOSS_P = Decimal('85')
MIN_LOSS_P = Decimal("-100")  # Adjust if you need a different minimum

PRECISION_2 = Decimal('100')
PRECISION_6 = Decimal('1000000')
PRECISION_9 = Decimal('1000000000')
PRECISION_12 = Decimal('1000000000000')
PRECISION_16 = Decimal('10000000000000000')
PRECISION_18 = Decimal('1000000000000000000')

LIQ_THRESHOLD_P = Decimal('90')  # -90% (of collateral)
