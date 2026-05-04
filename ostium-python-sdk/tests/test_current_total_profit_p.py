import pytest
from decimal import Decimal
from ostium_python_sdk.formulae import CurrentTotalProfitP

TEST_CASES = [
    {
        "case_name": "CASE-1",
        "total_profit": Decimal("346.777539"),
        "collateral": Decimal("500"),
        "expected_total_profit_p": Decimal("69.355507"),
    },
    {
        "case_name": "CASE-2",
        "total_profit": Decimal("-15.206703"),
        "collateral": Decimal("1"),
        "expected_total_profit_p": Decimal("-100"),
    },
    {
        "case_name": "CASE-3",
        "total_profit": Decimal("1000"),
        "collateral": Decimal("10"),
        "expected_total_profit_p": Decimal("10000"),
    },
    {
        "case_name": "CASE-4",
        "total_profit": Decimal("-21.90"),
        "collateral": Decimal("93.5"),
        "expected_total_profit_p": Decimal("-23.422459"),
    },
]


@pytest.mark.parametrize("case", TEST_CASES)
def test_current_total_profit_p(case):
    result_dec = CurrentTotalProfitP(case["total_profit"], case["collateral"])
    expected_dec = case["expected_total_profit_p"]
    assert result_dec == pytest.approx(expected_dec, abs=1e-6)
