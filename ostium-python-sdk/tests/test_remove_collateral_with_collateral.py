import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import RemoveCollateralWithCollateral

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "removed_collateral": Decimal("900"),
        "expected_leverage": Decimal("100"),
    },
    {
        "case_name": "CASE-2",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "removed_collateral": Decimal("0"),
        "expected_leverage": Decimal("10"),
    },
    {
        "case_name": "CASE-3",
        "leverage": Decimal("1"),
        "collateral": Decimal("1000"),
        "removed_collateral": Decimal("980"),
        "expected_leverage": Decimal("50"),
    },
    {
        "case_name": "CASE-4",
        "leverage": Decimal("8"),
        "collateral": Decimal("10000"),
        "removed_collateral": Decimal("8297.872341"),
        "expected_leverage": Decimal("47"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_remove_collateral_with_collateral(case):
    actual = RemoveCollateralWithCollateral(
        leverage=case["leverage"],
        collateral=case["collateral"],
        removed_collateral=case["removed_collateral"],
    )
    assert actual == pytest.approx(case["expected_leverage"], abs=1e-6)
