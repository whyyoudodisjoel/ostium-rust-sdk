import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import GetStopLossPrice

# Multiple test scenarios collected in a list of dictionaries
TEST_CASES = [
    # CASE-1: A long position with a 10% stop loss
    {
        "case_name": "CASE-1",
        "openPrice": Decimal("100"),
        "loss_p": Decimal("10"),
        "leverage": Decimal("10"),
        "isLong": True,
        "expected_sl_price": Decimal("99"),
    },
    # CASE-2: A short position with the same parameters
    {
        "case_name": "CASE-2",
        "openPrice": Decimal("100"),
        "loss_p": Decimal("10"),
        "leverage": Decimal("10"),
        "isLong": False,
        "expected_sl_price": Decimal("101"),
    },
    # You can add more cases here if desired
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_get_trade_sl_price(case):
    """
    A Pytest-based test for GetStopLossPrice, using parameterized scenarios
    with raw Decimal values (no parseUnits).
    """
    print(f"\n=> Running: {case['case_name']} => {case}")

    sl_price = GetStopLossPrice(
        case["openPrice"],
        case["loss_p"],
        case["leverage"],
        case["isLong"],
    )

    # Similar to unittest's assertAlmostEqual(..., places=7)
    assert sl_price == pytest.approx(case["expected_sl_price"], abs=1e-7), (
        f"{case['case_name']} failed: got {sl_price}, expected {case['expected_sl_price']}"
    )
