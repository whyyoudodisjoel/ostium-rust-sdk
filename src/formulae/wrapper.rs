//! Combine the formula primitives into the per-trade [`TradeMetrics`].

use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};

use crate::consts::{PRECISION_2, PRECISION_6, PRECISION_18};
use crate::formulae::{
    current_total_profit_raw, current_trade_profit_raw, get_current_rollover_fee, get_funding_rate,
    get_price_impact, get_total_profit_p, get_trade_funding_fee, get_trade_rollover_fee,
};
use crate::price::PriceEntry;
use crate::formulae::pairinfos::get_trade_liquidation_price;
use crate::subgraph::{DecExt, OpenTrade};

#[derive(Debug, Clone, Default)]
pub struct TradeMetrics {
    pub pnl: f64,
    pub pnl_percent: f64,
    pub rollover: f64,
    pub funding: f64,
    pub net_pnl: f64,
    pub net_value: f64,
    pub liquidation_price: f64,
    pub price_impact: f64,
    pub is_market_open: bool,
    pub bid: f64,
    pub mid: f64,
    pub ask: f64,
}

/// Compute open-trade metrics (PnL, funding, rollover, liquidation price,
/// price-impact-adjusted exit) for a single trade.
pub fn get_trade_metrics(
    trade: &OpenTrade,
    price_data: &PriceEntry,
    block_number: u64,
    pair_max_leverage: Decimal,
    liq_margin_threshold_p: Decimal,
) -> TradeMetrics {
    let pair = &trade.pair;

    let collateral = trade.collateral.dec();
    let leverage = trade.leverage.dec();
    let highest_leverage = trade.highest_leverage.dec();
    let open_price = trade.open_price.dec();
    let funding = trade.funding.dec();
    let rollover = trade.rollover.dec();

    let current_rollover_raw = get_current_rollover_fee(
        pair.acc_rollover.dec(),
        pair.last_rollover_block.dec(),
        pair.rollover_fee_per_block.dec(),
        Decimal::from(block_number),
    );

    tracing::debug!("current rollover fee: {}", current_rollover_raw);

    let trade_rollover_fee = get_trade_rollover_fee(
        rollover / PRECISION_18,
        current_rollover_raw / PRECISION_18,
        collateral / PRECISION_6,
        leverage / PRECISION_2,
    );

    tracing::debug!("trade rollover fee: {}", trade_rollover_fee);

    let funding_rate_raw = get_funding_rate(
        pair.acc_funding_long.dec(),
        pair.acc_funding_short.dec(),
        pair.last_funding_rate.dec(),
        pair.max_funding_fee_per_block.dec(),
        pair.last_funding_block.dec(),
        Decimal::from(block_number),
        pair.long_oi.dec(),
        pair.short_oi.dec(),
        pair.max_oi.dec(),
        pair.hill_inflection_point.dec(),
        pair.hill_pos_scale.dec(),
        pair.hill_neg_scale.dec(),
        pair.spring_factor.dec(),
        pair.s_factor_up_scale_p.dec(),
        pair.s_factor_down_scale_p.dec(),
    );

    let trade_funding_fee = get_trade_funding_fee(
        funding / PRECISION_18,
        if trade.is_buy {
            funding_rate_raw.acc_funding_long
        } else {
            funding_rate_raw.acc_funding_short
        },
        collateral / PRECISION_6,
        leverage / PRECISION_2,
    );

    let trade_liquidation_price = get_trade_liquidation_price(
        liq_margin_threshold_p / PRECISION_2,
        open_price / PRECISION_18,
        trade.is_buy,
        collateral / PRECISION_6,
        leverage / PRECISION_2,
        trade_rollover_fee,
        trade_funding_fee,
        pair_max_leverage,
    );

    let mid_v = Decimal::try_from(price_data.mid).unwrap_or(Decimal::ZERO);
    let bid_v = Decimal::try_from(price_data.bid).unwrap_or(Decimal::ZERO);
    let ask_v = Decimal::try_from(price_data.ask).unwrap_or(Decimal::ZERO);

    let price_impact_raw = get_price_impact(
        (mid_v * PRECISION_18).round_dp_with_strategy(0, RoundingStrategy::ToZero),
        (bid_v * PRECISION_18).round_dp_with_strategy(0, RoundingStrategy::ToZero),
        (ask_v * PRECISION_18).round_dp_with_strategy(0, RoundingStrategy::ToZero),
        false,
        trade.is_buy,
    );
    let price_after_impact = price_impact_raw.price_after_impact;

    let pnl_raw = current_trade_profit_raw(
        open_price / PRECISION_18,
        price_after_impact / PRECISION_18,
        trade.is_buy,
        leverage / PRECISION_2,
        highest_leverage / PRECISION_2,
        collateral / PRECISION_6,
    );

    let total_profit_raw = current_total_profit_raw(
        open_price / PRECISION_18,
        price_after_impact / PRECISION_18,
        trade.is_buy,
        leverage / PRECISION_2,
        highest_leverage / PRECISION_2,
        collateral / PRECISION_6,
        trade_rollover_fee,
        trade_funding_fee,
    );

    let pnl_percent_raw = get_total_profit_p(total_profit_raw, collateral / PRECISION_6);

    let collateral_dec = collateral / PRECISION_6;
    let net_value = (total_profit_raw + collateral_dec).to_f64().unwrap_or(0.0);
    let price_impact = (price_after_impact / PRECISION_18).to_f64().unwrap_or(0.0);

    TradeMetrics {
        pnl: pnl_raw.to_f64().unwrap_or(0.0),
        pnl_percent: pnl_percent_raw.to_f64().unwrap_or(0.0),
        rollover: trade_rollover_fee.to_f64().unwrap_or(0.0),
        funding: trade_funding_fee.to_f64().unwrap_or(0.0),
        net_pnl: total_profit_raw.to_f64().unwrap_or(0.0),
        net_value,
        liquidation_price: trade_liquidation_price.to_f64().unwrap_or(0.0),
        price_impact,
        is_market_open: price_data.is_market_open,
        bid: price_data.bid,
        mid: price_data.mid,
        ask: price_data.ask,
    }
}
