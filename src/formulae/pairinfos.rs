use rust_decimal::{Decimal, RoundingStrategy};

const RD: RoundingStrategy = RoundingStrategy::ToZero;

pub fn get_trade_liquidation_price(
    liq_margin_threshold_p: Decimal,
    open_price: Decimal,
    long: bool,
    collateral: Decimal,
    leverage: Decimal,
    rollover_fee: Decimal,
    funding_fee: Decimal,
    max_leverage: Decimal,
) -> Decimal {
    let raw_adjusted_threshold =
        (liq_margin_threshold_p * leverage / max_leverage).round_dp_with_strategy(6, RD);
    let liq_margin_value =
        (collateral * raw_adjusted_threshold).round_dp_with_strategy(6, RD);
    let target_collateral_after_fees = collateral - liq_margin_value - rollover_fee - funding_fee;
    let liq_price_distance = (open_price * target_collateral_after_fees / collateral / leverage)
        .round_dp_with_strategy(6, RD);
    let liq_price = if long {
        open_price - liq_price_distance
    } else {
        open_price + liq_price_distance
    };
    liq_price.max(Decimal::ZERO)
}

pub fn get_trade_liquidation_margin(
    liq_margin_threshold_p: Decimal,
    collateral: Decimal,
    leverage: Decimal,
    max_leverage: Decimal,
) -> Decimal {
    let raw_adjusted_threshold =
        (liq_margin_threshold_p * leverage / max_leverage).round_dp_with_strategy(6, RD);
    (collateral * raw_adjusted_threshold / Decimal::from(100)).round_dp_with_strategy(6, RD)
}

pub fn get_trade_value_pure(
    collateral: Decimal,
    percent_profit: Decimal,
    rollover_fee: Decimal,
    funding_fee: Decimal,
    liq_margin_value: Decimal,
) -> Decimal {
    let profit_part = (collateral * percent_profit / Decimal::from(100))
        .round_dp_with_strategy(6, RD);
    let value = collateral + profit_part - rollover_fee - funding_fee;
    if value <= liq_margin_value {
        return Decimal::ZERO;
    }
    value
}

pub fn get_trade_value(
    liq_margin_threshold_p: Decimal,
    collateral: Decimal,
    percent_profit: Decimal,
    rollover_fee: Decimal,
    funding_fee: Decimal,
    leverage: Decimal,
    max_leverage: Decimal,
) -> (Decimal, Decimal) {
    let liq_margin_value = get_trade_liquidation_margin(
        liq_margin_threshold_p,
        collateral,
        leverage,
        max_leverage,
    );
    let value = get_trade_value_pure(
        collateral,
        percent_profit,
        rollover_fee,
        funding_fee,
        liq_margin_value,
    );
    (value, liq_margin_value)
}

pub fn get_opening_fee(
    trade_size: Decimal,
    leverage: Decimal,
    oi_delta: Decimal,
    maker_max_leverage: Decimal,
    maker_fee_p: Decimal,
    taker_fee_p: Decimal,
) -> Decimal {
    let mut maker_amount = Decimal::ZERO;
    let mut taker_amount = Decimal::ZERO;

    if (oi_delta * trade_size) < Decimal::ZERO && leverage <= maker_max_leverage {
        if (oi_delta * (oi_delta + trade_size)) >= Decimal::ZERO {
            maker_amount = trade_size.abs();
        } else {
            maker_amount = oi_delta.abs();
            taker_amount = (oi_delta + trade_size).abs();
        }
    } else {
        taker_amount = trade_size.abs();
    }

    let base_fee = ((maker_fee_p * maker_amount).round_dp_with_strategy(6, RD)
        + (taker_fee_p * taker_amount).round_dp_with_strategy(6, RD))
        / Decimal::from(100);

    base_fee.round_dp_with_strategy(6, RD)
}
