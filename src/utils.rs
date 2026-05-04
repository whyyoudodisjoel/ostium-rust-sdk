//! Numeric helpers and the [`TradeParams`] builder.

use rust_decimal::{Decimal, RoundingStrategy};

use crate::ostium::OpenOrderType;

/// Period multiplier in `calculate_fee_per_hours`: `(10/3) * 60 * 60 * 100`
/// per hour. Pre-computed to avoid the divide each call.
fn period_for_hours(hours: u64) -> Decimal {
    (Decimal::from(hours) * Decimal::from(10))
        / Decimal::from(3)
        * Decimal::from(60)
        * Decimal::from(60)
        * Decimal::from(100)
}

/// Mirrors the Python `calculate_fee_per_hours`. Multiplies the funding rate
/// by `period_for_hours(hours)` and rounds to `precision` decimals using
/// banker's rounding.
pub fn calculate_fee_per_hours(
    cur_funding_rate: Decimal,
    hours: u64,
    round_to_precision: u32,
) -> Decimal {
    let rate = cur_funding_rate * period_for_hours(hours);
    rate.round_dp_with_strategy(round_to_precision, RoundingStrategy::MidpointNearestEven)
}

/// Convert a floating-point amount into the integer base units a contract
/// expects (e.g. USDC has 6 decimals, so `1.5` → `1_500_000`).
pub fn to_base_units(amount: Decimal, decimals: u32) -> u128 {
    let scaled = amount * Decimal::from(10u128.pow(decimals));
    use rust_decimal::prelude::ToPrimitive;
    scaled
        .round_dp_with_strategy(0, RoundingStrategy::ToZero)
        .to_u128()
        .unwrap_or(0)
}

/// Scale `value` first to `precision` decimals (rounded), then pad up to
/// `scale` decimals. Result is an integer-valued [`Decimal`].
pub fn convert_to_scaled_integer(value: Decimal, precision: u32, scale: u32) -> Decimal {
    debug_assert!(scale >= precision, "scale must be ≥ precision");
    let factor_p = Decimal::from(10u128.pow(precision));
    let precise_value =
        (value * factor_p).round_dp_with_strategy(0, RoundingStrategy::MidpointNearestEven);
    let factor_rest = Decimal::from(10u128.pow(scale - precision));
    precise_value * factor_rest
}

/// Convenience: `convert_to_scaled_integer(value, 5, 18)`.
pub fn convert_to_scaled_integer_default(value: Decimal) -> Decimal {
    convert_to_scaled_integer(value, 5, 18)
}

/// Parse a limit order ID like
/// `"0x3750a14869d419f1069cbf7cbe47a89b2dc1d4c4_0_0"` into
/// `(pair_index, index)`.
pub fn parse_limit_order_id(limit_order_id: &str) -> Option<(String, String)> {
    let parts: Vec<&str> = limit_order_id.split('_').collect();
    if parts.len() != 3 {
        return None;
    }
    Some((parts[1].to_string(), parts[2].to_string()))
}

/// Parameters for opening a new trade. Use [`TradeParams::builder`] to
/// construct.
#[derive(Debug, Clone)]
pub struct TradeParams {
    pub collateral: Decimal,
    pub leverage: Decimal,
    pub asset_type: u16,
    pub direction: bool,
    pub is_day_trade: bool,
    pub order_type: OpenOrderType,
    pub take_profit: Option<Decimal>,
    pub stop_loss: Option<Decimal>,
    pub trader_address: Option<alloy::primitives::Address>,
    pub builder_address: Option<alloy::primitives::Address>,
    pub builder_fee: Option<Decimal>,
}

impl TradeParams {
    pub fn builder() -> TradeParamsBuilder {
        TradeParamsBuilder::default()
    }

    /// `(tp, sl)` — `Decimal::ZERO` if unset, matching the on-chain encoding.
    pub fn tp_sl_prices(&self) -> (Decimal, Decimal) {
        (
            self.take_profit
                .filter(|v| !v.is_zero())
                .unwrap_or(Decimal::ZERO),
            self.stop_loss
                .filter(|v| !v.is_zero())
                .unwrap_or(Decimal::ZERO),
        )
    }
}

/// Builder for [`TradeParams`].
#[derive(Debug, Default, Clone)]
pub struct TradeParamsBuilder {
    collateral: Option<Decimal>,
    leverage: Option<Decimal>,
    asset_type: Option<u16>,
    direction: Option<bool>,
    is_day_trade: bool,
    order_type: OpenOrderType,
    take_profit: Option<Decimal>,
    stop_loss: Option<Decimal>,
    trader_address: Option<alloy::primitives::Address>,
    builder_address: Option<alloy::primitives::Address>,
    builder_fee: Option<Decimal>,
}

impl TradeParamsBuilder {
    pub fn collateral(mut self, v: Decimal) -> Self {
        self.collateral = Some(v);
        self
    }
    pub fn leverage(mut self, v: Decimal) -> Self {
        self.leverage = Some(v);
        self
    }
    pub fn pair(mut self, asset_type: u16) -> Self {
        self.asset_type = Some(asset_type);
        self
    }
    pub fn long(mut self) -> Self {
        self.direction = Some(true);
        self
    }
    pub fn short(mut self) -> Self {
        self.direction = Some(false);
        self
    }
    pub fn direction(mut self, is_long: bool) -> Self {
        self.direction = Some(is_long);
        self
    }
    pub fn is_day_trade(mut self, v: bool) -> Self {
        self.is_day_trade = v;
        self
    }
    pub fn order_type(mut self, v: OpenOrderType) -> Self {
        self.order_type = v;
        self
    }
    pub fn take_profit(mut self, v: Decimal) -> Self {
        self.take_profit = Some(v);
        self
    }
    pub fn stop_loss(mut self, v: Decimal) -> Self {
        self.stop_loss = Some(v);
        self
    }
    pub fn trader_address(mut self, v: alloy::primitives::Address) -> Self {
        self.trader_address = Some(v);
        self
    }
    pub fn builder_address(mut self, v: alloy::primitives::Address) -> Self {
        self.builder_address = Some(v);
        self
    }
    pub fn builder_fee(mut self, v: Decimal) -> Self {
        self.builder_fee = Some(v);
        self
    }

    pub fn build(self) -> Result<TradeParams, crate::error::OstiumError> {
        Ok(TradeParams {
            collateral: self
                .collateral
                .ok_or(crate::error::OstiumError::Builder("missing collateral"))?,
            leverage: self
                .leverage
                .ok_or(crate::error::OstiumError::Builder("missing leverage"))?,
            asset_type: self
                .asset_type
                .ok_or(crate::error::OstiumError::Builder("missing pair (asset_type)"))?,
            direction: self
                .direction
                .ok_or(crate::error::OstiumError::Builder("missing direction"))?,
            is_day_trade: self.is_day_trade,
            order_type: self.order_type,
            take_profit: self.take_profit,
            stop_loss: self.stop_loss,
            trader_address: self.trader_address,
            builder_address: self.builder_address,
            builder_fee: self.builder_fee,
        })
    }
}
