from ostium_python_sdk.scscript.pairinfos import getTradeValue
import pytest
from decimal import Decimal


# Global list of all test cases
test_cases = [
    # CASE-0
    {
        'liq_margin_threshold_p': Decimal('25'),  # 25 (no division needed)
        'collateral': Decimal('100'),  # 100000000 / PRECISION_6
        'percent_profit': Decimal('1'),  # 1000000 / PRECISION_6
        'rollover_fee': Decimal('0.000001'),  # 1 / PRECISION_6
        'funding_fee': Decimal('0'),  # 0 / PRECISION_6
        'leverage': Decimal('10'),  # 1000 / PRECISION_2
        'max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        # 100999999 / PRECISION_6
        'expected_trade_value': Decimal('100.999999'),
        'expected_liq_margin_value': Decimal('25'),  # 25000000 / PRECISION_6
    },
    # CASE-1
    {
        'liq_margin_threshold_p': Decimal('25'),  # 25 (no division needed)
        'collateral': Decimal('100'),  # 100000000 / PRECISION_6
        'percent_profit': Decimal('87.769211'),  # 87769211 / PRECISION_6
        'rollover_fee': Decimal('1.395969'),  # 1395969 / PRECISION_6
        'funding_fee': Decimal('2.145623'),  # 2145623 / PRECISION_6
        'leverage': Decimal('10'),  # 1000 / PRECISION_2
        'max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        # 184227619 / PRECISION_6
        'expected_trade_value': Decimal('184.227619'),
        'expected_liq_margin_value': Decimal('25'),  # 25000000 / PRECISION_6
    },
    # CASE-2
    {
        'liq_margin_threshold_p': Decimal('25'),  # 25 (no division needed)
        'collateral': Decimal('200'),  # 200000000 / PRECISION_6
        'percent_profit': Decimal('99.900994'),  # 99900994 / PRECISION_6
        'rollover_fee': Decimal('2.158825'),  # 2158825 / PRECISION_6
        'funding_fee': Decimal('3.366384'),  # 3366384 / PRECISION_6
        'leverage': Decimal('5'),  # 500 / PRECISION_2
        'max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        # 394276779 / PRECISION_6
        'expected_trade_value': Decimal('394.276779'),
        'expected_liq_margin_value': Decimal('25'),  # 25000000 / PRECISION_6
    },
    # CASE-3 - change liq margin threshold to 20%
    {
        'liq_margin_threshold_p': Decimal('20'),  # 25 (no division needed)
        'collateral': Decimal('200'),  # 200000000 / PRECISION_6
        'percent_profit': Decimal('99.900994'),  # 99900994 / PRECISION_6
        'rollover_fee': Decimal('2.158825'),  # 2158825 / PRECISION_6
        'funding_fee': Decimal('3.366384'),  # 3366384 / PRECISION_6
        'leverage': Decimal('5'),  # 500 / PRECISION_2
        'max_leverage': Decimal('10'),  # 1000 / PRECISION_2
        # 394276779 / PRECISION_6
        'expected_trade_value': Decimal('394.276779'),
        'expected_liq_margin_value': Decimal('20'),  # 25000000 / PRECISION_6
    }
]


@pytest.mark.parametrize("case", test_cases)
def test_get_trade_value(case):
    """Test multiple scenarios for getTradeValue with Pytest."""

    trade_value, liq_margin_value = getTradeValue(
        liqMarginThresholdP=case['liq_margin_threshold_p'],
        collateral=case['collateral'],
        percentProfit=case['percent_profit'],
        rolloverFee=case['rollover_fee'],
        fundingFee=case['funding_fee'],
        leverage=case['leverage'],
        maxLeverage=case['max_leverage']
    )

    # Assert trade value
    assert trade_value == pytest.approx(case['expected_trade_value'], abs=1e-5), \
        f"Trade value failed for case: {case}"

    # Assert liquidation margin value
    assert liq_margin_value == pytest.approx(case['expected_liq_margin_value'], abs=1e-5), \
        f"Liquidation margin value failed for case: {case}"
