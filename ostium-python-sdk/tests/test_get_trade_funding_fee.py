import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import GetTradeFundingFee

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "initial_funding": Decimal("0.00432345"),
        "current_funding": Decimal("0.00532355"),
        "collateral": Decimal("3000"),
        "leverage": Decimal("10"),
        "expected_funding_fee": Decimal("30.003"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_get_trade_funding_fee(case):
    actual = GetTradeFundingFee(
        initial_funding=case["initial_funding"],
        current_funding=case["current_funding"],
        collateral=case["collateral"],
        leverage=case["leverage"],
    )
    assert actual == pytest.approx(case["expected_funding_fee"], abs=1e-6)
