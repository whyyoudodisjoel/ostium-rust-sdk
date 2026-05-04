from ostium_python_sdk.scscript.funding import getPendingAccFundingFees
import pytest
from decimal import Decimal

# Constants for precision
PRECISION_18 = Decimal('1000000000000000000')  # 1e18
PRECISION_6 = Decimal('1000000')               # 1e6
PRECISION_2 = Decimal('100')                   # 1e2

# Global list of all test cases
test_cases = [
    # CASE-0
    {
        'blockNumber': Decimal('12000'),
        'lastUpdateBlock': Decimal('30'),
        'valueLong': Decimal('0') / PRECISION_18,
        'valueShort': Decimal('0') / PRECISION_18,
        'openInterestUsdcLong': Decimal('999999999') / PRECISION_6,
        'openInterestUsdcShort': Decimal('0') / PRECISION_6,
        'oiCap': Decimal('1000000000000') / PRECISION_6,
        'maxFundingFeePerBlock': Decimal('47564687975') / PRECISION_18,
        'lastFundingRate': Decimal('19609397') / PRECISION_18,
        'hillInflectionPoint': Decimal('160000000000000000') / PRECISION_18,
        'hillPosScale': Decimal('118') / PRECISION_2,
        'hillNegScale': Decimal('91') / PRECISION_2,
        'springFactor': Decimal('86000000000000') / PRECISION_18,
        'sFactorUpScale': Decimal('11000') / PRECISION_2,
        'sFactorDownScaleP': Decimal('9000') / PRECISION_2,
        'expected_acc_funding_long': Decimal('0.000045646799152794'),
        'expected_acc_funding_short': Decimal('0'),
        'expected_latest_funding_rate': Decimal('0.000000003929451136'),
    },
    # CASE-1
    {
        'blockNumber': Decimal('100'),
        'lastUpdateBlock': Decimal('30'),
        'valueLong': Decimal('0') / PRECISION_18,
        'valueShort': Decimal('0') / PRECISION_18,
        'openInterestUsdcLong': Decimal('999999999') / PRECISION_6,
        'openInterestUsdcShort': Decimal('0') / PRECISION_6,
        'oiCap': Decimal('1000000000000') / PRECISION_6,
        'maxFundingFeePerBlock': Decimal('47564687975') / PRECISION_18,
        'lastFundingRate': Decimal('19609397') / PRECISION_18,
        'hillInflectionPoint': Decimal('160000000000000000') / PRECISION_18,
        'hillPosScale': Decimal('118') / PRECISION_2,
        'hillNegScale': Decimal('91') / PRECISION_2,
        'springFactor': Decimal('86000000000000') / PRECISION_18,
        'sFactorUpScale': Decimal('11000') / PRECISION_2,
        'sFactorDownScaleP': Decimal('9000') / PRECISION_2,
        'expected_acc_funding_long': Decimal('0.000000002969071461'),
        'expected_acc_funding_short': Decimal('0'),
        'expected_latest_funding_rate': Decimal('0.000000000065175499'),
    },
    # CASE-2
    {
        'blockNumber': Decimal('12000'),
        'lastUpdateBlock': Decimal('200'),
        'valueLong': Decimal('12722273808') / PRECISION_18,
        'valueShort': Decimal('0') / PRECISION_18,
        'openInterestUsdcLong': Decimal('966666666') / PRECISION_6,
        'openInterestUsdcShort': Decimal('499999999') / PRECISION_6,
        'oiCap': Decimal('1000000000000') / PRECISION_6,
        'maxFundingFeePerBlock': Decimal('47564687975') / PRECISION_18,
        'lastFundingRate': Decimal('129795925') / PRECISION_18,
        'hillInflectionPoint': Decimal('160000000000000000') / PRECISION_18,
        'hillPosScale': Decimal('118') / PRECISION_2,
        'hillNegScale': Decimal('91') / PRECISION_2,
        'springFactor': Decimal('86000000000000') / PRECISION_18,
        'sFactorUpScale': Decimal('11000') / PRECISION_2,
        'sFactorDownScaleP': Decimal('9000') / PRECISION_2,
        'expected_acc_funding_long': Decimal('0.000045715898199632'),
        'expected_acc_funding_short': Decimal('-0.000088359473572374'),
        'expected_latest_funding_rate': Decimal('0.000000003922567501'),
    }
]


@pytest.mark.parametrize("test_case", test_cases)
def test_get_pending_acc_funding_fees(test_case):
    """Test getPendingAccFundingFees function with various test cases"""
    # Call the function with test case parameters
    acc_funding_long, acc_funding_short, latest_funding_rate, target_funding_rate = getPendingAccFundingFees(
        blockNumber=test_case['blockNumber'],
        lastUpdateBlock=test_case['lastUpdateBlock'],
        valueLong=test_case['valueLong'],
        valueShort=test_case['valueShort'],
        openInterestUsdcLong=test_case['openInterestUsdcLong'],
        openInterestUsdcShort=test_case['openInterestUsdcShort'],
        OiCap=test_case['oiCap'],
        maxFundingFeePerBlock=test_case['maxFundingFeePerBlock'],
        lastFundingRate=test_case['lastFundingRate'],
        hillInflectionPoint=test_case['hillInflectionPoint'],
        hillPosScale=test_case['hillPosScale'],
        hillNegScale=test_case['hillNegScale'],
        springFactor=test_case['springFactor'],
        sFactorUpScale=test_case['sFactorUpScale'],
        sFactorDownScaleP=test_case['sFactorDownScaleP']
    )

    # Print results for debugging
    print(f"\nTest Case Results:")
    print(f"acc_funding_long: {acc_funding_long}")
    print(f"acc_funding_short: {acc_funding_short}")
    print(f"latest_funding_rate: {latest_funding_rate}")
    print(f"target_funding_rate: {target_funding_rate}")
    # Assertions
    assert acc_funding_long == pytest.approx(test_case['expected_acc_funding_long'], rel=Decimal('1e-12')), \
        f"acc_funding_long {acc_funding_long} != {test_case['expected_acc_funding_long']}"

    assert acc_funding_short == pytest.approx(test_case['expected_acc_funding_short'], rel=Decimal('1e-12')), \
        f"acc_funding_short {acc_funding_short} != {test_case['expected_acc_funding_short']}"

    assert latest_funding_rate == pytest.approx(test_case['expected_latest_funding_rate'], rel=Decimal('1e-12')), \
        f"latest_funding_rate {latest_funding_rate} != {test_case['expected_latest_funding_rate']}"
