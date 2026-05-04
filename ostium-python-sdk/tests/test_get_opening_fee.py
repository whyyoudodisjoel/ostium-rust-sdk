from ostium_python_sdk.scscript.pairinfos import getOpeningFee
import pytest
from decimal import Decimal


# Global list of all test cases
test_cases = [
    # CASE-0 - test_Validate_Full_Taker_getOpeningFee
    {
        'trade_size': Decimal('-10000'),
        'leverage': Decimal('3'),
        'oi_delta': Decimal('5000'),
        'maker_max_leverage': Decimal('10'),
        'maker_fee_p': Decimal('0.0001'),  # 100 / PRECISION_6 => 0.0001
        'taker_fee_p': Decimal('0.0003'),  # 300 / PRECISION_6 => 0.0003
        'expected_fee': Decimal('0.02')
    },
    # CASE-1 - test_Validate_Negative_OiDelta_Full_Maker_getOpeningFee
    {
        'trade_size': Decimal('10'),  # 10000000 / PRECISION_6
        'leverage': Decimal('3'),  # 300 / PRECISION_2
        'oi_delta': Decimal('-5000'),  # -5000000000 / PRECISION_6
        'maker_max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        'maker_fee_p': Decimal('0.0001'),  # 100 / PRECISION_6
        'taker_fee_p': Decimal('0.0003'),  # 300 / PRECISION_6
        'expected_fee': Decimal('0.000010')
    },
    # CASE-2 - test_Validate_Negative_OiDelta_Maker_And_Taker_getOpeningFee
    {
        'trade_size': Decimal('10'),  # 10000000 / PRECISION_6
        'leverage': Decimal('3'),  # 300 / PRECISION_2
        'oi_delta': Decimal('-5'),  # -5000000 / PRECISION_6
        'maker_max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        'maker_fee_p': Decimal('0.0001'),  # 100 / PRECISION_6
        'taker_fee_p': Decimal('0.0003'),  # 300 / PRECISION_6
        'expected_fee': Decimal('0.000020')
    },
    # CASE-3 - test_Validate_Negative_OiDelta_Lower_Fees_getOpeningFee
    {
        'trade_size': Decimal('10'),  # 10000000 / PRECISION_6
        'leverage': Decimal('3'),  # 300 / PRECISION_2
        'oi_delta': Decimal('-5'),  # -5000000 / PRECISION_6
        'maker_max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        'maker_fee_p': Decimal('0.00005'),  # 50 / PRECISION_6
        'taker_fee_p': Decimal('0.0002'),  # 200 / PRECISION_6
        'expected_fee': Decimal('0.000012')
    }
]


@pytest.mark.parametrize("case", test_cases)
def test_get_opening_fee(case):
    """Test multiple scenarios for getOpeningFee with Pytest."""

    fee = getOpeningFee(
        tradeSize=case['trade_size'],
        leverage=case['leverage'],
        oiDelta=case['oi_delta'],
        makerMaxLeverage=case['maker_max_leverage'],
        makerFeeP=case['maker_fee_p'],
        takerFeeP=case['taker_fee_p']
    )

    # Equivalent to assertAlmostEqual(..., places=5) is approx with abs=1e-5
    # or thereabouts. Adjust as needed for your precision.
    assert fee == pytest.approx(case['expected_fee'], abs=1e-5), \
        f"Failed for case: {case}"
