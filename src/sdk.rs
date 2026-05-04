//! Top-level [`OstiumSDK`] and its [`OstiumSDKBuilder`].

use std::str::FromStr;

use alloy::primitives::Address;
use alloy::providers::{DynProvider, Provider, ProviderBuilder};
use alloy::signers::local::PrivateKeySigner;
use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};
use url::Url;

use crate::config::NetworkConfig;
use crate::consts::{
    CHAIN_ID_ARB_MAINNET, CHAIN_ID_ARB_TESTNET, PRECISION_2, PRECISION_6, PRECISION_9,
    PRECISION_12, PRECISION_18,
};
use crate::error::{OstiumError, Result};
use crate::faucet::Faucet;
use crate::formulae::funding::get_target_funding_rate;
use crate::formulae::get_funding_rate;
use crate::formulae::{TradeMetrics, get_trade_metrics};
use crate::ostium::Ostium;
use crate::price::Price;
use crate::subgraph::{DecExt, DecOptExt, OpenTrade, SubgraphClient};
use crate::utils::calculate_fee_per_hours;

/// Network selector — pick mainnet/testnet by enum or pass a custom config.
#[derive(Debug, Clone)]
pub enum Network {
    Mainnet,
    Testnet,
    Custom(NetworkConfig),
}

/// Backwards-compat type alias matching pre-refactor naming.
pub type NetworkSpec = Network;

impl<'a> std::convert::TryFrom<&'a str> for Network {
    type Error = OstiumError;
    fn try_from(s: &'a str) -> Result<Self> {
        match s {
            "mainnet" => Ok(Network::Mainnet),
            "testnet" => Ok(Network::Testnet),
            other => Err(OstiumError::UnsupportedNetwork(other.to_string())),
        }
    }
}

impl From<NetworkConfig> for Network {
    fn from(cfg: NetworkConfig) -> Self {
        Network::Custom(cfg)
    }
}

impl Network {
    fn name(&self) -> &'static str {
        match self {
            Network::Mainnet => "mainnet",
            Network::Testnet => "testnet",
            Network::Custom(c) => {
                if c.is_testnet {
                    "testnet"
                } else {
                    "mainnet"
                }
            }
        }
    }

    fn into_config(self) -> NetworkConfig {
        match self {
            Network::Mainnet => NetworkConfig::mainnet(),
            Network::Testnet => NetworkConfig::testnet(),
            Network::Custom(c) => c,
        }
    }
}

/// Top-level SDK aggregating the on-chain client, subgraph, price feed, and
/// optional faucet.
pub struct OstiumSDK {
    pub use_delegation: bool,
    pub rpc_url: String,
    pub network_config: NetworkConfig,
    pub provider: DynProvider,
    pub ostium: Ostium,
    pub subgraph: SubgraphClient,
    pub price: Price,
    /// Only set when running on testnet.
    pub faucet: Option<Faucet>,
}

impl OstiumSDK {
    /// Begin constructing an [`OstiumSDK`].
    pub fn builder() -> OstiumSDKBuilder {
        OstiumSDKBuilder::default()
    }

    /// Get open trades for `trader`, defaulting to the SDK's wallet address.
    pub async fn get_open_trades(
        &self,
        trader_address: Option<Address>,
    ) -> Result<(Vec<OpenTrade>, Address)> {
        let trader = match trader_address {
            Some(a) => a,
            None => self.ostium.public_address()?,
        };
        tracing::debug!("trader public address: {:?}", trader);
        let trades = self.subgraph.get_open_trades(&format!("{:?}", trader)).await?;
        Ok((trades, trader))
    }

    /// Compute live metrics for a single open trade (PnL, funding, rollover,
    /// liquidation price).
    pub async fn get_open_trade_metrics(
        &self,
        pair_id: u64,
        trade_index: u64,
        trader_address: Option<Address>,
    ) -> Result<TradeMetrics> {
        let (open_trades, trader) = self.get_open_trades(trader_address).await?;

        let liq_margin_threshold_p = self.subgraph.get_liq_margin_threshold_p().await?;
        tracing::debug!(
            "liq_margin_threshold_p: {} (used for liquidation price)",
            liq_margin_threshold_p
        );

        if open_trades.is_empty() {
            return Err(OstiumError::NoOpenTrades(trader));
        }

        let trade = open_trades
            .into_iter()
            .find(|t| {
                t.pair.id.parse::<u64>().ok() == Some(pair_id)
                    && t.index.parse::<u64>().ok() == Some(trade_index)
            })
            .ok_or(OstiumError::TradeNotFound {
                trader,
                pair_id,
                index: trade_index,
            })?;

        let price_data = self.price.get_latest_price(&trade.pair.from, &trade.pair.to).await?;
        let block_number = self.ostium.block_number().await?;
        let pair_max_leverage = self.get_pair_max_leverage(&trade.pair.id).await?;

        Ok(get_trade_metrics(
            &trade,
            &price_data,
            block_number,
            pair_max_leverage,
            liq_margin_threshold_p,
        ))
    }

    /// Compute the target funding rate for a pair.
    pub async fn get_target_funding_rate(&self, pair_id: &str) -> Result<Decimal> {
        let pair = self.subgraph.get_pair_details(pair_id).await?;

        let hill_inflection_point = pair.hill_inflection_point.dec() / PRECISION_18;
        let max_funding_fee_per_block = pair.max_funding_fee_per_block.dec() / PRECISION_18;
        let hill_pos_scale = pair.hill_pos_scale.dec() / PRECISION_2;
        let hill_neg_scale = pair.hill_neg_scale.dec() / PRECISION_2;

        let curr_long_oi = pair.long_oi.dec() / PRECISION_6;
        let curr_short_oi = pair.short_oi.dec() / PRECISION_6;
        let max_oi = pair.max_oi.dec() / PRECISION_6;

        let open_interest_max = curr_long_oi.max(curr_short_oi);
        let denom = max_oi
            .max(open_interest_max)
            .round_dp_with_strategy(6, RoundingStrategy::ToZero);
        let normalized_oi_delta = ((curr_long_oi - curr_short_oi)
            .round_dp_with_strategy(6, RoundingStrategy::ToZero)
            / denom)
            .round_dp_with_strategy(6, RoundingStrategy::ToZero);

        let target = get_target_funding_rate(
            normalized_oi_delta,
            hill_inflection_point,
            max_funding_fee_per_block,
            hill_pos_scale,
            hill_neg_scale,
        );

        tracing::debug!(
            "{}{} target funding rate: {}",
            pair.from,
            pair.to,
            target
        );

        Ok(target)
    }

    /// Maximum leverage allowed for overnight (stock-style) trades, if set.
    pub async fn get_pair_overnight_max_leverage(
        &self,
        pair_id: &str,
    ) -> Result<Option<Decimal>> {
        let pair = self.subgraph.get_pair_details(pair_id).await?;
        Ok(pair
            .overnight_max_leverage
            .dec_opt()
            .filter(|v| !v.is_zero())
            .map(|v| v / PRECISION_2))
    }

    /// Maximum leverage for the pair, falling back to the group's max.
    pub async fn get_pair_max_leverage(&self, pair_id: &str) -> Result<Decimal> {
        let pair = self.subgraph.get_pair_details(pair_id).await?;
        let group_max = pair.group.max_leverage.dec();
        Ok(if group_max.is_zero() {
            pair.max_leverage.dec() / PRECISION_2
        } else {
            group_max / PRECISION_2
        })
    }

    /// Rollover fee accrual rate over `period_hours`.
    pub async fn get_rollover_rate_for_pair_id(
        &self,
        pair_id: &str,
        period_hours: u64,
    ) -> Result<Decimal> {
        let pair = self.subgraph.get_pair_details(pair_id).await?;
        let rollover_fee_per_block = pair.rollover_fee_per_block.dec() / PRECISION_18;
        Ok(calculate_fee_per_hours(rollover_fee_per_block, period_hours, 5))
    }

    /// `(acc_funding_long, acc_funding_short, funding_rate, target_funding_rate)`
    /// scaled to `period_hours`.
    pub async fn get_funding_rate_for_pair_id(
        &self,
        pair_id: &str,
        period_hours: u64,
    ) -> Result<(Decimal, Decimal, f64, f64)> {
        let pair = self.subgraph.get_pair_details(pair_id).await?;
        let block_number = self.ostium.block_number().await?;

        let last_trade_price = pair.last_trade_price.dec();
        let long_oi = pair.long_oi.dec();
        let short_oi = pair.short_oi.dec();

        let long_oi_calc = (long_oi * last_trade_price) / PRECISION_18 / PRECISION_12;
        let short_oi_calc = (short_oi * last_trade_price) / PRECISION_18 / PRECISION_12;
        let long_oi_int = long_oi_calc
            .round_dp_with_strategy(0, RoundingStrategy::ToZero)
            .to_string();
        let short_oi_int = short_oi_calc
            .round_dp_with_strategy(0, RoundingStrategy::ToZero)
            .to_string();

        let ret = get_funding_rate(
            pair.acc_funding_long.dec(),
            pair.acc_funding_short.dec(),
            pair.last_funding_rate.dec(),
            pair.max_funding_fee_per_block.dec(),
            pair.last_funding_block.dec(),
            Decimal::from(block_number),
            Decimal::from_str(&long_oi_int).map_err(|e| OstiumError::Conversion(e.to_string()))?,
            Decimal::from_str(&short_oi_int).map_err(|e| OstiumError::Conversion(e.to_string()))?,
            pair.max_oi.dec(),
            pair.hill_inflection_point.dec(),
            pair.hill_pos_scale.dec(),
            pair.hill_neg_scale.dec(),
            pair.spring_factor.dec(),
            pair.s_factor_up_scale_p.dec(),
            pair.s_factor_down_scale_p.dec(),
        );

        let multiplier = (10.0_f64 / 3.0) * 60.0 * 60.0 * 100.0 * period_hours as f64;
        let funding_rate = ret.latest_funding_rate.to_f64().unwrap_or(0.0) * multiplier;
        let target_funding_rate = ret.target_funding_rate.to_f64().unwrap_or(0.0) * multiplier;

        tracing::debug!(
            "{}{} funding rate ({}h): {}% target: {}%",
            pair.from,
            pair.to,
            period_hours,
            funding_rate,
            target_funding_rate
        );

        Ok((
            ret.acc_funding_long,
            ret.acc_funding_short,
            funding_rate,
            target_funding_rate,
        ))
    }

    /// Scaled, sorted snapshot of every pair, optionally augmented with the
    /// current price feed.
    pub async fn get_formatted_pairs_details(
        &self,
        including_current_price_and_market_status: bool,
    ) -> Result<Vec<FormattedPair>> {
        let pairs = self.subgraph.get_pairs().await?;
        let mut formatted: Vec<FormattedPair> = Vec::with_capacity(pairs.len());

        for pair in pairs.into_iter() {
            let group_max = pair.group.max_leverage.dec();
            let max_leverage = if group_max.is_zero() {
                pair.max_leverage.dec() / PRECISION_2
            } else {
                group_max / PRECISION_2
            };
            let overnight = pair
                .overnight_max_leverage
                .dec_opt()
                .filter(|v| !v.is_zero())
                .map(|v| v / PRECISION_2);

            let mut entry = FormattedPair {
                id: pair.id.parse().unwrap_or(0),
                from: pair.from.clone(),
                to: pair.to.clone(),
                group: pair.group.name,
                long_oi: pair.long_oi.dec() / PRECISION_18,
                short_oi: pair.short_oi.dec() / PRECISION_18,
                max_oi: pair.max_oi.dec() / PRECISION_6,
                maker_fee_p: pair.maker_fee_p.dec() / PRECISION_6,
                taker_fee_p: pair.taker_fee_p.dec() / PRECISION_6,
                max_leverage,
                maker_max_leverage: pair.maker_max_leverage.dec() / PRECISION_2,
                group_max_collateral_p: pair.group.max_collateral_p.dec() / PRECISION_2,
                min_lev_pos: pair.fee.min_lev_pos.dec() / PRECISION_6,
                last_funding_rate: pair.last_funding_rate.dec() / PRECISION_9,
                cur_funding_long: pair.cur_funding_long.dec() / PRECISION_9,
                cur_funding_short: pair.cur_funding_short.dec() / PRECISION_9,
                last_funding_block: pair.last_funding_block.parse().unwrap_or(0),
                overnight_max_leverage: overnight,
                price: None,
                is_market_open: None,
                is_day_trading_closed: None,
            };

            if including_current_price_and_market_status {
                if let Ok((price, is_market_open, is_day_trading_closed)) =
                    self.price.get_price(&pair.from, &pair.to).await
                {
                    entry.price = Some(price);
                    entry.is_market_open = Some(is_market_open);
                    entry.is_day_trading_closed = Some(is_day_trading_closed);
                }
            }

            formatted.push(entry);
        }

        formatted.sort_by_key(|p| p.id);
        Ok(formatted)
    }
}

/// Per-pair snapshot returned by [`OstiumSDK::get_formatted_pairs_details`].
#[derive(Debug, Clone)]
pub struct FormattedPair {
    pub id: u64,
    pub from: String,
    pub to: String,
    pub group: String,
    pub long_oi: Decimal,
    pub short_oi: Decimal,
    pub max_oi: Decimal,
    pub maker_fee_p: Decimal,
    pub taker_fee_p: Decimal,
    pub max_leverage: Decimal,
    pub maker_max_leverage: Decimal,
    pub group_max_collateral_p: Decimal,
    pub min_lev_pos: Decimal,
    pub last_funding_rate: Decimal,
    pub cur_funding_long: Decimal,
    pub cur_funding_short: Decimal,
    pub last_funding_block: u64,
    pub overnight_max_leverage: Option<Decimal>,
    pub price: Option<f64>,
    pub is_market_open: Option<bool>,
    pub is_day_trading_closed: Option<bool>,
}

/// Builder for [`OstiumSDK`]. Required: [`network`](Self::network) and
/// [`rpc_url`](Self::rpc_url) (the latter falls back to the `RPC_URL`
/// environment variable).
#[derive(Default)]
pub struct OstiumSDKBuilder {
    network: Option<Network>,
    rpc_url: Option<String>,
    private_key: Option<String>,
    signer: Option<PrivateKeySigner>,
    use_delegation: bool,
}

impl OstiumSDKBuilder {
    pub fn network(mut self, network: impl Into<Network>) -> Self {
        self.network = Some(network.into());
        self
    }

    pub fn rpc_url(mut self, rpc_url: String) -> Self {
        self.rpc_url = Some(rpc_url);
        self
    }

    /// Set a private key as a hex string. Convenience for env-var driven setups.
    pub fn private_key_hex(mut self, pk: impl Into<String>) -> Self {
        self.private_key = Some(pk.into());
        self
    }

    /// Set the signer directly.
    pub fn signer(mut self, signer: PrivateKeySigner) -> Self {
        self.signer = Some(signer);
        self
    }

    pub fn use_delegation(mut self, v: bool) -> Self {
        self.use_delegation = v;
        self
    }

    pub async fn build(self) -> Result<OstiumSDK> {
        let network = self
            .network
            .ok_or(OstiumError::Builder("missing network"))?;
        let rpc_url = self
            .rpc_url
            .or_else(|| std::env::var("RPC_URL").ok())
            .ok_or_else(|| OstiumError::MissingRpcUrl {
                network: match &network {
                    Network::Mainnet => "mainnet",
                    Network::Testnet => "testnet",
                    Network::Custom(c) => {
                        if c.is_testnet {
                            "testnet"
                        } else {
                            "mainnet"
                        }
                    }
                },
            })?;

        let signer = match (self.signer, self.private_key) {
            (Some(s), _) => Some(s),
            (None, Some(hex)) => Some(
                PrivateKeySigner::from_str(&hex)
                    .map_err(|e| OstiumError::InvalidPrivateKey(e.to_string()))?,
            ),
            (None, None) => match std::env::var("PRIVATE_KEY") {
                Ok(hex) => Some(
                    PrivateKeySigner::from_str(&hex)
                        .map_err(|e| OstiumError::InvalidPrivateKey(e.to_string()))?,
                ),
                Err(_) => None,
            },
        };

        let net_name = network.name();
        let network_config = network.into_config();

        let url = Url::parse(&rpc_url)?;
        let provider = ProviderBuilder::new().connect_http(url).erased();

        let actual = provider
            .get_chain_id()
            .await
            .map_err(|e| OstiumError::Contract(e.to_string()))?;
        let expected = if network_config.is_testnet {
            CHAIN_ID_ARB_TESTNET
        } else {
            CHAIN_ID_ARB_MAINNET
        };
        if actual != expected {
            return Err(OstiumError::ChainIdMismatch {
                expected,
                actual,
                network: if network_config.is_testnet {
                    "testnet"
                } else {
                    "mainnet"
                },
            });
        }

        tracing::debug!(
            "network: {} (chain id {}, RPC {}, name {})",
            if network_config.is_testnet { "TESTNET" } else { "MAINNET" },
            actual,
            rpc_url,
            net_name
        );

        let ostium = Ostium::new(
            provider.clone(),
            network_config.contracts.usdc,
            network_config.contracts.trading_storage,
            network_config.contracts.trading,
            signer.clone(),
            self.use_delegation,
        );

        let subgraph = SubgraphClient::new(network_config.graph_url.to_string());
        let price = Price::new();
        let faucet = if network_config.is_testnet {
            Some(Faucet::new(provider.clone(), signer))
        } else {
            None
        };

        Ok(OstiumSDK {
            use_delegation: self.use_delegation,
            rpc_url,
            network_config,
            provider,
            ostium,
            subgraph,
            price,
            faucet,
        })
    }
}
