import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import CurrentTradeProfitP

# List of test scenarios
TEST_CASES = [
    {
        "case_name": "CASE-1",
        "open_price": Decimal("1824.6"),
        "current_price": Decimal("1985.4"),
        "long": True,
        "leverage": Decimal("10"),
        "highest_leverage": Decimal("10"),
        "expected_profit_p": Decimal("88.128904"),
    },
    {
        "case_name": "CASE-2",
        "open_price": Decimal("1345.6"),
        "current_price": Decimal("1349.2"),
        "long": False,
        "leverage": Decimal("2"),
        "highest_leverage": Decimal("2"),
        "expected_profit_p": Decimal("-0.535077"),
    },
    {
        "case_name": "CASE-3",
        "open_price": Decimal("12450"),
        "current_price": Decimal("13020"),
        "long": False,
        "leverage": Decimal("5"),
        "highest_leverage": Decimal("5"),
        "expected_profit_p": Decimal("-22.891566"),
    },
    {
        "case_name": "CASE-4",
        "open_price": Decimal("100"),
        "current_price": Decimal("101"),
        "long": True,
        "leverage": Decimal("10"),
        "highest_leverage": Decimal("10"),
        "expected_profit_p": Decimal("10"),
    },
    {
        "case_name": "CASE-5",
        "open_price": Decimal("100"),
        "current_price": Decimal("99"),
        "long": False,
        "leverage": Decimal("10"),
        "highest_leverage": Decimal("10"),
        "expected_profit_p": Decimal("10"),
    },
    {
        "case_name": "CASE-6",
        "open_price": Decimal("100"),
        "current_price": Decimal("99"),
        "long": True,
        "leverage": Decimal("10"),
        "highest_leverage": Decimal("10"),
        "expected_profit_p": Decimal("-10"),
    },
    {
        "case_name": "CASE-7",
        "open_price": Decimal("100"),
        "current_price": Decimal("101"),
        "long": False,
        "leverage": Decimal("10"),
        "highest_leverage": Decimal("10"),
        "expected_profit_p": Decimal("-10"),
    },
    {
        "case_name": "CASE-8",
        "open_price": Decimal("1550.97411212"),
        "current_price": Decimal("1552.47324651"),
        "long": True,
        "leverage": Decimal("100"),
        "highest_leverage": Decimal("100"),
        "expected_profit_p": Decimal("9.665760"),
    },
    {
        "case_name": "CASE-9",
        "open_price": Decimal("100"),
        "current_price": Decimal("1000"),
        "long": True,
        "leverage": Decimal("1"),
        "highest_leverage": Decimal("1"),
        "expected_profit_p": Decimal("900"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_current_trade_profit_p(case):
    """
    Tests for the CurrentTradeProfitP function, based on
    the scenario data from your TypeScript test suite.
    """
    print(f"\n==> Running {case['case_name']}: {case}")

    actual_profit_p = CurrentTradeProfitP(
        open_price=case["open_price"],
        current_price=case["current_price"],
        long=case["long"],
        leverage=case["leverage"],
        highest_leverage=case["highest_leverage"],
    )

    # Compare with expected_profit_p using an absolute tolerance
    assert actual_profit_p == pytest.approx(case["expected_profit_p"], abs=1e-6), (
        f"{case['case_name']} failed: got {actual_profit_p}, "
        f"expected {case['expected_profit_p']}"
    )
