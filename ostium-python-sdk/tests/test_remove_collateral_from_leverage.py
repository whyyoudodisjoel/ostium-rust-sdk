import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import RemoveCollateralFromLeverage

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("100"),
        "expected_collateral": Decimal("900"),
    },
    {
        "case_name": "CASE-2",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("10"),
        "expected_collateral": Decimal("0"),
    },
    {
        "case_name": "CASE-3",
        "leverage": Decimal("1"),
        "collateral": Decimal("1000"),
        "desired_leverage": Decimal("50"),
        "expected_collateral": Decimal("980"),
    },
    {
        "case_name": "CASE-4",
        "leverage": Decimal("8"),
        "collateral": Decimal("10000"),
        "desired_leverage": Decimal("47"),
        "expected_collateral": Decimal("8297.872341"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_remove_collateral_from_leverage(case):
    actual = RemoveCollateralFromLeverage(
        leverage=case["leverage"],
        desired_leverage=case["desired_leverage"],
        collateral=case["collateral"],
    )
    assert actual == pytest.approx(case["expected_collateral"], abs=1e-6)
