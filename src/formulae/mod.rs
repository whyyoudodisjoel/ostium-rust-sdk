//! Pure formula primitives (PnL, funding-rate, price-impact, liquidation
//! price). These have no I/O and live in dedicated submodules:
//!
//! - [`funding`]: target funding rate + accrued funding-rate per-block.
//! - [`pairinfos`]: per-trade liquidation price / margin / opening fee
//!   (mirroring the `OstiumPairInfos` script in the python sdk).
//! - [`wrapper`]: stitches the above together into a per-trade
//!   [`wrapper::TradeMetrics`] snapshot.

use rust_decimal::Decimal;
use rust_decimal_macros::dec;

use crate::consts::{MAX_PROFIT_P, MIN_LOSS_P, PRECISION_2, PRECISION_6, PRECISION_18};

pub mod funding;
pub mod pairinfos;
pub mod wrapper;

pub use funding::get_pending_acc_funding_fees;
pub use wrapper::{TradeMetrics, get_trade_metrics};

pub struct PriceImpact {
    pub price_impact_p: Decimal,
    pub price_after_impact: Decimal,
}

pub fn get_take_profit_price(
    open_price: Decimal,
    profit_p: Decimal,
    leverage: Decimal,
    is_long: bool,
) -> Decimal {
    let price_diff = (open_price * profit_p) / (leverage * dec!(100));
    let tp_price = if is_long { open_price + price_diff } else { open_price - price_diff };
    tp_price.abs()
}

pub fn get_stop_loss_price(
    open_price: Decimal,
    loss_p: Decimal,
    leverage: Decimal,
    is_long: bool,
) -> Decimal {
    let price_diff = (open_price * loss_p) / (leverage * dec!(100));
    let sl_price = if is_long { open_price - price_diff } else { open_price + price_diff };
    sl_price.abs()
}

pub fn current_trade_profit_p(
    open_price: Decimal,
    current_price: Decimal,
    long: bool,
    leverage: Decimal,
    highest_leverage: Decimal,
) -> Decimal {
    let leverage_to_use = leverage.max(highest_leverage);

    let price_diff = if long {
        current_price - open_price
    } else {
        open_price - current_price
    };

    let profit_p = ((price_diff / open_price) * leverage_to_use * dec!(100)).min(MAX_PROFIT_P)
        * (leverage / leverage_to_use);

    profit_p
}

pub fn topup_with_collateral(
    leverage: Decimal,
    collateral: Decimal,
    added_collateral: Decimal,
) -> Decimal {
    (collateral * leverage) / (collateral + added_collateral)
}

pub fn topup_with_leverage(
    leverage: Decimal,
    desired_leverage: Decimal,
    collateral: Decimal,
) -> Decimal {
    (collateral * leverage) / (desired_leverage - collateral)
}

pub fn remove_collateral_with_collateral(
    leverage: Decimal,
    collateral: Decimal,
    removed_collateral: Decimal,
) -> Decimal {
    (collateral * leverage) / (collateral - removed_collateral)
}

pub fn remove_collateral_from_leverage(
    leverage: Decimal,
    desired_leverage: Decimal,
    collateral: Decimal,
) -> Decimal {
    collateral - (collateral * leverage / desired_leverage)
}

pub fn get_current_rollover_fee(
    acc_rollover: Decimal,
    last_rollover_block: Decimal,
    roll_over_fee_per_block: Decimal,
    latest_block: Decimal,
) -> Decimal {
    acc_rollover + (latest_block - last_rollover_block * roll_over_fee_per_block)
}

pub fn get_trade_rollover_fee(
    trade_rollover: Decimal,
    current_rollover: Decimal,
    collateral: Decimal,
    leverage: Decimal,
) -> Decimal {
    (current_rollover - trade_rollover) * collateral * leverage
}

pub fn get_trade_funding_fee(
    initial_funding: Decimal,
    current_funding: Decimal,
    collateral: Decimal,
    leverage: Decimal,
) -> Decimal {
    (current_funding - initial_funding) * collateral * leverage
}

pub fn get_price_impact(
    mid_price: Decimal,
    bid_price: Decimal,
    ask_price: Decimal,
    is_open: bool,
    is_long: bool,
) -> PriceImpact {
    if mid_price == Decimal::ZERO {
        return PriceImpact {
            price_impact_p: Decimal::ZERO,
            price_after_impact: Decimal::ZERO,
        };
    }

    let above_spot = is_open == is_long;
    let used_price = if above_spot { ask_price } else { bid_price };
    let price_impact_p = Decimal::from(100) * ((mid_price - used_price).abs() / mid_price);

    PriceImpact {
        price_impact_p,
        price_after_impact: used_price,
    }
}

pub fn current_trade_profit_raw(
    open_price: Decimal,
    current_price: Decimal,
    long: bool,
    leverage: Decimal,
    highest_leverage: Decimal,
    collateral: Decimal,
) -> Decimal {
    let profit_p = current_trade_profit_p(open_price, current_price, long, leverage, highest_leverage);
    (collateral * profit_p) / Decimal::from(100)
}

pub fn current_total_profit_raw(
    open_price: Decimal,
    current_price: Decimal,
    long: bool,
    leverage: Decimal,
    highest_leverage: Decimal,
    collateral: Decimal,
    rollover_fee: Decimal,
    funding_fee: Decimal,
) -> Decimal {
    let trade_profit = current_trade_profit_raw(
        open_price,
        current_price,
        long,
        leverage,
        highest_leverage,
        collateral,
    );
    trade_profit - rollover_fee - funding_fee
}

pub fn get_total_profit_p(total_profit: Decimal, collateral: Decimal) -> Decimal {
    (total_profit * Decimal::from(100) / collateral).max(MIN_LOSS_P)
}

pub struct FundingRateData {
    pub acc_funding_long: Decimal,
    pub acc_funding_short: Decimal,
    pub latest_funding_rate: Decimal,
    pub target_funding_rate: Decimal,
}

pub fn get_funding_rate(
    acc_per_oi_long: Decimal,
    acc_per_oi_short: Decimal,
    last_funding_rate: Decimal,
    max_funding_fee_per_block: Decimal,
    last_update_block: Decimal,
    latest_block: Decimal,
    oi_long: Decimal,
    oi_short: Decimal,
    oi_cap: Decimal,
    hill_inflection_point: Decimal,
    hill_pos_scale: Decimal,
    hill_neg_scale: Decimal,
    spring_factor: Decimal,
    s_factor_upscale_p: Decimal,
    s_factor_downscale_p: Decimal,
) -> FundingRateData {
    let (acc_funding_long, acc_funding_short, latest_funding_rate, target_funding_rate) =
        get_pending_acc_funding_fees(
            latest_block,
            last_update_block,
            acc_per_oi_long / PRECISION_18,
            acc_per_oi_short / PRECISION_18,
            oi_long / PRECISION_6,
            oi_short / PRECISION_6,
            oi_cap / PRECISION_6,
            max_funding_fee_per_block / PRECISION_18,
            last_funding_rate / PRECISION_18,
            hill_inflection_point / PRECISION_18,
            hill_pos_scale / PRECISION_2,
            hill_neg_scale / PRECISION_2,
            spring_factor / PRECISION_18,
            s_factor_upscale_p / PRECISION_2,
            s_factor_downscale_p / PRECISION_2,
        );

    FundingRateData {
        acc_funding_long,
        acc_funding_short,
        latest_funding_rate,
        target_funding_rate,
    }
}
