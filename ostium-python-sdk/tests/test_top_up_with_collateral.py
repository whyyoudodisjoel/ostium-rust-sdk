import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import TopUpWithCollateral

TEST_CASES = [
    # CASE-1
    {
        "case_name": "CASE-1",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "added_collateral": Decimal("1000"),
        "expected_leverage": Decimal("5"),
    },
    # CASE-2
    {
        "case_name": "CASE-2",
        "leverage": Decimal("10"),
        "collateral": Decimal("1000"),
        "added_collateral": Decimal("0"),
        "expected_leverage": Decimal("10"),
    },
    # CASE-3
    {
        "case_name": "CASE-3",
        "leverage": Decimal("50"),
        "collateral": Decimal("1000"),
        "added_collateral": Decimal("49000"),
        "expected_leverage": Decimal("1"),
    },
    # CASE-4
    {
        "case_name": "CASE-4",
        "leverage": Decimal("47"),
        "collateral": Decimal("10000"),
        "added_collateral": Decimal("48750"),
        "expected_leverage": Decimal("8"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_top_up_with_collateral(case):
    actual_leverage = TopUpWithCollateral(
        case["leverage"],
        case["collateral"],
        case["added_collateral"]
    )

    assert actual_leverage == pytest.approx(case["expected_leverage"], abs=1e-6), (
        f"{case['case_name']} failed: got {actual_leverage}, "
        f"expected {case['expected_leverage']}"
    )
