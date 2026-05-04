import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import CurrentTradeProfitRaw

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "open_price": Decimal("1530"),
        "current_price": Decimal("1550"),
        "long": True,
        "leverage": Decimal("30"),
        "highest_leverage": Decimal("30"),
        "collateral": Decimal("500"),
        "expected_profit": Decimal("196.078430"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_current_trade_profit_raw(case):
    actual = CurrentTradeProfitRaw(
        open_price=case["open_price"],
        current_price=case["current_price"],
        long=case["long"],
        leverage=case["leverage"],
        highest_leverage=case["highest_leverage"],
        collateral=case["collateral"],
    )
    assert actual == pytest.approx(case["expected_profit"], abs=1e-5)
