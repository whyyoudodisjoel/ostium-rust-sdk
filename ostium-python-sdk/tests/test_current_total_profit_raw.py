import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import CurrentTotalProfitRaw

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "open_price": Decimal("1493.3"),
        "current_price": Decimal("1528.21"),
        "long": True,
        "leverage": Decimal("20"),
        "highest_leverage": Decimal("20"),
        "collateral": Decimal("500"),
        "rollover_fee": Decimal("32"),
        "funding_fee": Decimal("-145"),
        "expected_total_profit": Decimal("346.777535"),
    },
    {
        "case_name": "CASE-2",
        "open_price": Decimal("1253"),
        "current_price": Decimal("1260"),
        "long": True,
        "leverage": Decimal("500"),
        "highest_leverage": Decimal("500"),
        "collateral": Decimal("1"),
        "rollover_fee": Decimal("23"),
        "funding_fee": Decimal("-5"),
        "expected_total_profit": Decimal("-15.206704"),
    },
    {
        "case_name": "CASE-3",
        "open_price": Decimal("73000"),
        "current_price": Decimal("71000"),
        "long": True,
        "leverage": Decimal("20"),
        "highest_leverage": Decimal("20"),
        "collateral": Decimal("10000"),
        "rollover_fee": Decimal("0"),
        "funding_fee": Decimal("0"),
        "expected_total_profit": Decimal("-5479.452000"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_current_total_profit_raw(case):
    actual = CurrentTotalProfitRaw(
        open_price=case["open_price"],
        current_price=case["current_price"],
        long=case["long"],
        leverage=case["leverage"],
        highest_leverage=case["highest_leverage"],
        collateral=case["collateral"],
        rollover_fee=case["rollover_fee"],
        funding_fee=case["funding_fee"],
    )
    assert actual == pytest.approx(case["expected_total_profit"], abs=1e-4)
