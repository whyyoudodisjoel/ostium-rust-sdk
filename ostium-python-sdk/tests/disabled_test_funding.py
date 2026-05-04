import pytest
from decimal import Decimal, getcontext
from ostium_python_sdk.scscript.funding import getPendingAccFundingFees


@pytest.mark.asyncio
async def test_get_pending_acc_funding_fees_longs_pay_shorts():
    """
    When 1 block has passed, oi delta null, spring factor scaled down -
    Should calculate correct funding rates: longs pay shorts.
    """

    # Set high precision for Decimal calculations
    getcontext().prec = 64

    # -----------------------------------------------------------
    # 1. Define input parameters (matching TypeScript parseUnits())
    # -----------------------------------------------------------
    acc_per_oi_long = Decimal('0')  # parseUnits('0', 18)
    acc_per_oi_short = Decimal('0')  # parseUnits('0', 18)
    last_funding_rate = Decimal('0')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('100') * Decimal('1000000')
    oi_short = Decimal('100') * Decimal('1000000')
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # -----------------------------------------------------------
    # 2. Define the expected outputs from the TypeScript test
    # -----------------------------------------------------------
    expected_latest_funding_rate = Decimal('0.000000024999937501')
    expected_acc_funding_long = Decimal('0.000000012499979000')
    expected_acc_funding_short = Decimal('-0.000000012499979000')
    expected_target_fr = Decimal('0.005')
    # -----------------------------------------------------------
    # 3. Call getPendingAccFundingFees
    #    (Note that this function typically returns a tuple of:
    #     (accFundingLong, accFundingShort, latestFundingRate[, targetFr?])
    # -----------------------------------------------------------
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # -----------------------------------------------------------
    # 5. Verify output matches expected (approximately)
    # -----------------------------------------------------------
    assert acc_funding_long == pytest.approx(expected_acc_funding_long, rel=Decimal('1e-12')), \
        f"acc_funding_long is {acc_funding_long}, expected {expected_acc_funding_long}"

    assert acc_funding_short == pytest.approx(expected_acc_funding_short, rel=Decimal('1e-12')), \
        f"acc_funding_short is {acc_funding_short}, expected {expected_acc_funding_short}"

    assert latest_funding_rate_out == pytest.approx(expected_latest_funding_rate, rel=Decimal('1e-12')), \
        f"latest_funding_rate is {latest_funding_rate_out}, expected {expected_latest_funding_rate}"

    assert target_fr_out == pytest.approx(expected_target_fr, rel=Decimal('1e-12')), \
        f"target_fr is {target_fr_out}, expected {expected_target_fr}"


@pytest.mark.asyncio
async def test_get_pending_acc_funding_fees_longs_pay_shorts_block_1_oi_delta_positive_normal_spring_factor():
    """
    When 1 block has passed, oidelta > 0, normal spring factor -
    Should calculate correct funding rates: longs pay shorts.
    """

    # Set precision
    getcontext().prec = 64

    # 1. Define input parameters, mirroring your TS scenario #2
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('0')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('500') * Decimal('1000000')   # parseUnits('500', 6)
    oi_short = Decimal('100') * Decimal('1000000')  # parseUnits('100', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Define the expected output values
    expected_latest_funding_rate = Decimal('0.000000025079471975')
    expected_acc_funding_long = Decimal('0.000000012539746270')
    expected_acc_funding_short = Decimal('-0.000000062698731350')
    expected_target_fr = Decimal('0.005015906934548239')

    # 3. Call the target function (which returns 4 values)
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Verify each output
    assert acc_funding_long == pytest.approx(expected_acc_funding_long, rel=Decimal('1e-12')), \
        f"acc_funding_long {acc_funding_long} != {expected_acc_funding_long}"
    assert acc_funding_short == pytest.approx(expected_acc_funding_short, rel=Decimal('1e-12')), \
        f"acc_funding_short {acc_funding_short} != {expected_acc_funding_short}"
    assert latest_funding_rate_out == pytest.approx(expected_latest_funding_rate, rel=Decimal('1e-12')), \
        f"latest_funding_rate {latest_funding_rate_out} != {expected_latest_funding_rate}"
    assert target_fr_out == pytest.approx(expected_target_fr, rel=Decimal('1e-12')), \
        f"target_fr {target_fr_out} != {expected_target_fr}"


@pytest.mark.asyncio
async def test_get_pending_acc_funding_fees_longs_pay_shorts_block_1_oi_delta_positive_sign_switched_spring_factor_scaled_up():
    """
    When 1 block has passed, oidelta > 0 and sign switched, scaled up spring factor -
    Should calculate correct funding rates: longs pay shorts.
    """

    # Set precision
    getcontext().prec = 64

    # 1. Define input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    # parseUnits('-0.000000000000000001', 18)
    last_funding_rate = Decimal('-0.000000000000000001')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('500') * Decimal('1000000')   # parseUnits('500', 6)
    oi_short = Decimal('100') * Decimal('1000000')  # parseUnits('100', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')        # sFactorUpScaleP
    s_factor_down_scale_p = Decimal('90')     # sFactorDownScaleP

    # 2. Define the expected outputs
    expected_latest_funding_rate = Decimal('0.000000032603289113')
    expected_acc_funding_long = Decimal('0.000000016301662040')
    expected_acc_funding_short = Decimal('-0.000000081508310200')
    expected_target_fr = Decimal('0.005015906934548239')

    # 3. Call the target function (4 values returned)
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Verify each output
    assert acc_funding_long == pytest.approx(expected_acc_funding_long, rel=Decimal('1e-12')), \
        f"acc_funding_long {acc_funding_long} != {expected_acc_funding_long}"
    assert acc_funding_short == pytest.approx(expected_acc_funding_short, rel=Decimal('1e-12')), \
        f"acc_funding_short {acc_funding_short} != {expected_acc_funding_short}"
    assert latest_funding_rate_out == pytest.approx(expected_latest_funding_rate, rel=Decimal('1e-12')), \
        f"latest_funding_rate {latest_funding_rate_out} != {expected_latest_funding_rate}"
    assert target_fr_out == pytest.approx(expected_target_fr, rel=Decimal('1e-12')), \
        f"target_fr {target_fr_out} != {expected_target_fr}"


@pytest.mark.asyncio
async def test_oi_delta_positive_scaled_down_spring_factor_longs_pay_shorts():
    """
    When 1 block has passed, oidelta > 0, scaled down spring factor -
    Should calculate correct funding rates: longs pay shorts.
    """

    getcontext().prec = 64

    # 1. Define input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('0.006')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('500') * Decimal('1000000')   # parseUnits('500', 6)
    oi_short = Decimal('100') * Decimal('1000000')  # parseUnits('100', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Expected outputs
    expected_latest_funding_rate = Decimal('0.005999995571591169')
    expected_acc_funding_long = Decimal('0.005999997785794101')
    expected_acc_funding_short = Decimal('-0.029999988928970505')
    expected_target_fr = Decimal('0.005015906934548239')

    # 3. Call function
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Assertions
    assert latest_funding_rate_out == pytest.approx(
        expected_latest_funding_rate, rel=Decimal('1e-12'))
    assert acc_funding_long == pytest.approx(
        expected_acc_funding_long, rel=Decimal('1e-12'))
    assert acc_funding_short == pytest.approx(
        expected_acc_funding_short, rel=Decimal('1e-12'))
    assert target_fr_out == pytest.approx(
        expected_target_fr, rel=Decimal('1e-12'))


@pytest.mark.asyncio
async def test_oi_delta_negative_normal_spring_factor_shorts_pay_longs():
    """
    When 1 block has passed, oidelta < 0, normal spring factor -
    Should calculate correct funding rates: shorts pay longs.
    """

    getcontext().prec = 64

    # 1. Define input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('0')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('1000') * Decimal('1000000')    # parseUnits('1000', 6)
    # parseUnits('100000', 6)
    oi_short = Decimal('100000') * Decimal('1000000')
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Expected outputs
    expected_latest_funding_rate = Decimal('-0.000000249274246362')
    expected_acc_funding_long = Decimal('-0.0000124637225383')
    expected_acc_funding_short = Decimal('0.000000124637225383')
    expected_target_fr = Decimal('-0.049854973909462642')

    # 3. Call function
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Assertions
    assert latest_funding_rate_out == pytest.approx(
        expected_latest_funding_rate, rel=Decimal('1e-12'))
    assert acc_funding_long == pytest.approx(
        expected_acc_funding_long, rel=Decimal('1e-12'))
    assert acc_funding_short == pytest.approx(
        expected_acc_funding_short, rel=Decimal('1e-12'))
    assert target_fr_out == pytest.approx(
        expected_target_fr, rel=Decimal('1e-12'))


@pytest.mark.asyncio
async def test_oi_delta_negative_sign_switched_scaled_up_spring_factor_shorts_pay_longs():
    """
    When 1 block has passed, oidelta < 0 and sign switched, scaled up spring factor -
    Should calculate correct funding rates: shorts pay longs.
    """

    getcontext().prec = 64

    # 1. Define input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('0.000000000000000001')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('1000') * Decimal('1000000')   # parseUnits('1000', 6)
    oi_short = Decimal('10000') * Decimal('1000000')  # parseUnits('10000', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Expected outputs
    expected_latest_funding_rate = Decimal('-0.000000022186178317')
    expected_acc_funding_long = Decimal('-0.000000110931010550')
    expected_acc_funding_short = Decimal('0.000000011093101055')
    expected_target_fr = Decimal('-0.003413269295780419')

    # 3. Call function
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Assertions
    assert latest_funding_rate_out == pytest.approx(
        expected_latest_funding_rate, rel=Decimal('1e-12'))
    assert acc_funding_long == pytest.approx(
        expected_acc_funding_long, rel=Decimal('1e-12'))
    assert acc_funding_short == pytest.approx(
        expected_acc_funding_short, rel=Decimal('1e-12'))
    assert target_fr_out == pytest.approx(
        expected_target_fr, rel=Decimal('1e-12'))


@pytest.mark.asyncio
async def test_oi_delta_negative_scaled_down_spring_factor_shorts_pay_longs():
    """
    When 1 block has passed, oidelta < 0, scaled down spring factor -
    Should calculate correct funding rates: shorts pay longs.
    """

    getcontext().prec = 64

    # 1. Input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('-0.005')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('1')
    oi_long = Decimal('100') * Decimal('1000000')   # parseUnits('100', 6)
    oi_short = Decimal('10000') * Decimal('1000000')  # parseUnits('10000', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Expected outputs
    expected_latest_funding_rate = Decimal(
        '-0.004999999444615238')
    expected_acc_funding_long = Decimal(
        '-0.499999972230743300')
    expected_acc_funding_short = Decimal('0.004999999722307433')
    expected_target_fr = Decimal('-0.004876580886315063')

    # 3. Call function
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Assertions
    assert latest_funding_rate_out == pytest.approx(
        expected_latest_funding_rate, rel=Decimal('1e-12'))
    assert acc_funding_long == pytest.approx(
        expected_acc_funding_long, rel=Decimal('1e-12'))
    assert acc_funding_short == pytest.approx(
        expected_acc_funding_short, rel=Decimal('1e-12'))
    assert target_fr_out == pytest.approx(
        expected_target_fr, rel=Decimal('1e-12'))


@pytest.mark.asyncio
async def test_blocks_10000000_oi_delta_null_longs_pay_shorts():
    """
    When 10000 block has passed, oi delta null -
    Should calculate correct funding rates: longs pay shorts.
    """

    getcontext().prec = 64

    # 1. Input parameters
    acc_per_oi_long = Decimal('0')
    acc_per_oi_short = Decimal('0')
    last_funding_rate = Decimal('0')
    max_funding_fee_per_block = Decimal('0.05')
    last_update_block = Decimal('0')
    latest_block = Decimal('10000000')
    oi_long = Decimal('100') * Decimal('1000000')   # parseUnits('100', 6)
    oi_short = Decimal('100') * Decimal('1000000')  # parseUnits('100', 6)
    oi_cap = Decimal('100000') * Decimal('1000000')
    hill_inflection_point = Decimal('0.1')
    hill_pos_scale = Decimal('0.94')
    hill_neg_scale = Decimal('1.15')
    spring_factor = Decimal('0.000005')
    s_factor_up_scale = Decimal('130')
    s_factor_down_scale_p = Decimal('90')

    # 2. Expected outputs
    expected_target_fr = Decimal('0.005')
    expected_latest_funding_rate = expected_target_fr
    expected_acc_funding_long = Decimal('49000')
    expected_acc_funding_short = Decimal('-49000')

    # 3. Call function
    acc_funding_long, acc_funding_short, latest_funding_rate_out, target_fr_out = getPendingAccFundingFees(
        blockNumber=latest_block,
        lastUpdateBlock=last_update_block,
        valueLong=acc_per_oi_long,
        valueShort=acc_per_oi_short,
        openInterestUsdcLong=oi_long,
        openInterestUsdcShort=oi_short,
        OiCap=oi_cap,
        maxFundingFeePerBlock=max_funding_fee_per_block,
        lastFundingRate=last_funding_rate,
        hillInflectionPoint=hill_inflection_point,
        hillPosScale=hill_pos_scale,
        hillNegScale=hill_neg_scale,
        springFactor=spring_factor,
        sFactorUpScale=s_factor_up_scale,
        sFactorDownScaleP=s_factor_down_scale_p
    )

    # 4. Assertions
    assert target_fr_out == pytest.approx(
        expected_target_fr, rel=Decimal('1e-12'))
    assert acc_funding_long == pytest.approx(
        expected_acc_funding_long, rel=Decimal('1e-12'))
    assert acc_funding_short == pytest.approx(
        expected_acc_funding_short, rel=Decimal('1e-12'))
    assert latest_funding_rate_out == pytest.approx(
        expected_latest_funding_rate, rel=Decimal('1e-12'))
