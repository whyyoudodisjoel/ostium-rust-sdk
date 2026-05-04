import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import TopUpWithLeverage

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("5"),
        "expected_added_collateral": Decimal("1000"),
    },
    {
        "case_name": "CASE-2",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("10"),
        "expected_added_collateral": Decimal("0"),
    },
    {
        "case_name": "CASE-3",
        "leverage": Decimal("50"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("1"),
        "expected_added_collateral": Decimal("49000"),
    },
    {
        "case_name": "CASE-4",
        "leverage": Decimal("47"),
        "collateral": Decimal("10000"),
        "desired_leverage": Decimal("8"),
        "expected_added_collateral": Decimal("48750"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_top_up_with_leverage(case):
    actual = TopUpWithLeverage(
        leverage=case["leverage"],
        desired_leverage=case["desired_leverage"],
        collateral=case["collateral"],
    )

    assert actual == pytest.approx(case["expected_added_collateral"], abs=1e-6)
