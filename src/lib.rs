//! # Ostium SDK
//!
//! A Rust SDK for the [Ostium](https://ostium.io) decentralized perpetual
//! trading platform on Arbitrum.
//!
//! Provides:
//! - On-chain client for opening/closing trades, managing positions, and
//!   approving USDC (via [`OstiumClient`]).
//! - GraphQL subgraph client returning typed responses (via
//!   [`SubgraphClient`]).
//! - REST price-feed client (via [`Price`]).
//! - Pure formula helpers for funding rate, PnL, liquidation price, etc.
//!
//! ## Quick start
//!
//! ```no_run
//! # async fn run() -> Result<(), ositum_sdk::OstiumError> {
//! use ositum_sdk::{OstiumSDK, Network};
//!
//! let sdk = OstiumSDK::builder()
//!     .network(Network::Mainnet)
//!     .rpc_url("https://arb1.arbitrum.io/rpc".to_string())
//!     .build()
//!     .await?;
//!
//! let pairs = sdk.get_formatted_pairs_details(false).await?;
//! println!("{} pairs", pairs.len());
//! # Ok(()) }
//! ```

pub mod config;
pub mod consts;
pub mod contracts;
pub mod error;
pub mod faucet;
pub mod formulae;
pub mod ostium;
pub mod price;
pub mod sdk;
pub mod subgraph;
pub mod utils;

// Public re-exports.
pub use config::{Contracts, NetworkConfig};
pub use error::{OstiumError, Result};
pub use faucet::Faucet;
pub use formulae::TradeMetrics;
pub use ostium::{
    CloseMarketTimeoutOutcome, OpenMarketTimeoutOutcome, OpenOrderType, Ostium as OstiumClient,
    TrackedOrder, TradeOutcome,
};
pub use price::Price;
pub use sdk::{Network, NetworkSpec, OstiumSDK, OstiumSDKBuilder};
pub use subgraph::{
    DecExt, DecOptExt, HistoryOrder, LimitOrder, OpenTrade, OrderRecord, Pair, PairFee, PairGroup,
    PairListEntry, SubgraphClient, TradeRecord,
};
pub use utils::TradeParams;
