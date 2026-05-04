import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import GetTradeRolloverFee

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "trade_rollover": Decimal("0.00432345"),
        "current_rollover": Decimal("0.00532355"),
        "collateral": Decimal("3000"),
        "leverage": Decimal("10"),
        "expected_rollover_fee": Decimal("30.003"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_get_trade_rollover_fee(case):
    actual = GetTradeRolloverFee(
        trade_rollover=case["trade_rollover"],
        current_rollover=case["current_rollover"],
        collateral=case["collateral"],
        leverage=case["leverage"],
    )
    assert actual == pytest.approx(case["expected_rollover_fee"], abs=1e-6)
