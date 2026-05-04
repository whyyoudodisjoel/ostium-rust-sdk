import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import GetTakeProfitPrice

# Combined scenarios in a single list of dictionaries
TEST_CASES = [
    # Existing Original Example
    {
        "case_name": "ORIGINAL-CASE",
        "openPrice": Decimal("100000"),
        "leverage": Decimal("100"),
        "isLong": True,
        "profit_p": Decimal("900"),
        "expected_tp_price": Decimal("109000"),
    },

    # CASE-1
    {
        "case_name": "CASE-1",
        "openPrice": Decimal("100"),
        "profit_p": Decimal("10"),
        "leverage": Decimal("10"),
        "isLong": True,
        "expected_tp_price": Decimal("101"),
    },
    # CASE-2
    {
        "case_name": "CASE-2",
        "openPrice": Decimal("100"),
        "profit_p": Decimal("10"),
        "leverage": Decimal("10"),
        "isLong": False,
        "expected_tp_price": Decimal("99"),
    },
    # CASE-3
    {
        "case_name": "CASE-3",
        "openPrice": Decimal("100"),
        "profit_p": Decimal("900"),
        "leverage": Decimal("5"),
        "isLong": False,
        "expected_tp_price": Decimal("0"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_get_trade_tp_price(case):
    """
    A Pytest-based test for GetTakeProfitPrice, using parameterized scenarios
    with raw Decimal values (no multiplying by 10^18, etc.).
    """
    print(f"\n=> Running: {case['case_name']} => {case}")

    # Please ensure your GetTakeProfitPrice signature matches the arguments below.
    tp_price = GetTakeProfitPrice(
        case["openPrice"],
        case["profit_p"],
        case["leverage"],
        # If your function doesn't need `isLong` again, remove it.
        case["isLong"],
    )

    # Equivalent to "assertAlmostEqual(..., places=7)" from unittest
    assert tp_price == pytest.approx(case["expected_tp_price"], abs=1e-7), (
        f"{case['case_name']} failed: got {tp_price}, expected {case['expected_tp_price']}"
    )
