from ostium_python_sdk.scscript.pairinfos import getTradeLiquidationPrice
import pytest
from decimal import Decimal


# Global list of all test cases
test_cases = [
    # CASE-0
    {
        'liq_margin_threshold_p': Decimal(0.25),  # 25%
        'openPrice': Decimal("100"),
        'isLong': True,
        'collateral': Decimal("10"),
        'leverage': Decimal("2"),
        'rollover_fee': Decimal('1'),
        'funding_fee': Decimal('1'),
        'max_leverage': Decimal(10),
        'expected_liq_price': Decimal('62.50')
    },
    # CASE-1
    {
        'liq_margin_threshold_p': Decimal(0.25),  # 25%
        "openPrice":  Decimal("1823.52"),
        "isLong": False,
        "collateral": Decimal("1000"),
        "leverage":   Decimal("100"),
        "rollover_fee": Decimal("10"),
        "funding_fee": Decimal("-4"),
        'max_leverage': Decimal(10),
        "expected_liq_price": Decimal("1796.057789"),
    },
    # CASE-2
    {
        'liq_margin_threshold_p': Decimal(0.1),  # 10%
        "openPrice":  Decimal("129.4"),
        "isLong": True,
        "collateral": Decimal("250"),
        "leverage":   Decimal("20"),
        "rollover_fee": Decimal("5"),
        "funding_fee": Decimal("2"),
        'max_leverage': Decimal(10),
        "expected_liq_price": Decimal("124.405160"),
    },
    # CASE-3
    {
        'liq_margin_threshold_p': Decimal(0.1),  # 10%
        "openPrice":  Decimal("27.2"),
        "isLong": False,
        "collateral": Decimal("100"),
        "leverage":   Decimal("2"),
        "rollover_fee": Decimal("2"),
        "funding_fee": Decimal("-0.5"),
        'max_leverage': Decimal(10),
        "expected_liq_price": Decimal("40.324000"),
    },
    # CASE-4
    {
        'liq_margin_threshold_p': Decimal(0.1),  # 10%
        "openPrice":  Decimal("1.34"),
        "isLong": False,
        "collateral": Decimal("1000"),
        "leverage":   Decimal("50"),
        "rollover_fee": Decimal("23"),
        "funding_fee": Decimal("1"),
        'max_leverage': Decimal(10),
        "expected_liq_price": Decimal("1.352756"),
    },
    {
        'liq_margin_threshold_p': Decimal(0.1),  # 10%
        "openPrice":  Decimal("8704.50"),
        "isLong": True,
        "collateral": Decimal("99"),
        "leverage":   Decimal("20"),
        "rollover_fee": Decimal("0"),
        "funding_fee": Decimal("0"),
        'max_leverage': Decimal(10),
        "expected_liq_price": Decimal("8356.320000"),
    },
]


@pytest.mark.parametrize("case", test_cases)
def test_trade_liquidation_price(case):
    """Test multiple scenarios for getTradeLiquidationPrice with Pytest."""

    # Optionally print the case for debugging
    print(f"\n\n===> case: {case}")

    liq_price = getTradeLiquidationPrice(
        liqMarginThresholdP=case['liq_margin_threshold_p'],
        openPrice=case['openPrice'],
        long=case['isLong'],
        collateral=case['collateral'],
        leverage=case['leverage'],
        rolloverFee=case['rollover_fee'],
        fundingFee=case['funding_fee'],
        maxLeverage=case['max_leverage']
    )

    # Equivalent to assertAlmostEqual(..., places=5) is approx with abs=1e-5
    # or thereabouts. Adjust as needed for your precision.
    assert liq_price == pytest.approx(case['expected_liq_price'], abs=1e-5), \
        f"Failed for case: {case}"
