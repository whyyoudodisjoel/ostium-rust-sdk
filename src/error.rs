//! Error type returned by the SDK.

use alloy::primitives::Address;

/// Result alias used throughout the crate.
pub type Result<T, E = OstiumError> = std::result::Result<T, E>;

/// Errors produced by the Ostium SDK.
#[derive(Debug, thiserror::Error)]
pub enum OstiumError {
    /// A write operation was attempted without a private key/signer being set.
    #[error("private key is required for Ostium platform write-operations")]
    MissingPrivateKey,

    /// `RPC_URL` was not provided and no environment variable was set.
    #[error(
        "no RPC_URL provided for {network}. Please provide via constructor or RPC_URL environment variable"
    )]
    MissingRpcUrl { network: &'static str },

    /// The supplied private key string could not be parsed.
    #[error("invalid private key: {0}")]
    InvalidPrivateKey(String),

    /// The supplied address could not be parsed.
    #[error("invalid address: {0}")]
    InvalidAddress(String),

    /// The chain reported by the RPC does not match the network.
    #[error(
        "chain ID mismatch. Expected {expected} for {network}, but RPC is connected to chain ID {actual}. Please check your RPC_URL."
    )]
    ChainIdMismatch {
        expected: u64,
        actual: u64,
        network: &'static str,
    },

    /// `network` argument was not "mainnet" or "testnet".
    #[error("unsupported network: {0}. Use 'mainnet' or 'testnet'")]
    UnsupportedNetwork(String),

    /// Builder pattern was used incorrectly (e.g. missing required field).
    #[error("builder error: {0}")]
    Builder(&'static str),

    /// HTTP transport error talking to the subgraph or price feed.
    #[error("http error: {0}")]
    Http(#[from] reqwest::Error),

    /// JSON (de)serialization error.
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),

    /// URL parsing error.
    #[error("url error: {0}")]
    Url(#[from] url::ParseError),

    /// The subgraph returned a non-2xx status.
    #[error("subgraph query failed with status {0}")]
    SubgraphStatus(u16),

    /// The subgraph returned a `errors` field in its response.
    #[error("subgraph errors: {0}")]
    SubgraphErrors(String),

    /// The subgraph response was missing data we expected.
    #[error("subgraph response missing field: {0}")]
    SubgraphMissingField(&'static str),

    /// No price could be found for the requested pair.
    #[error("no price found for pair: {from}/{to}")]
    PriceNotFound { from: String, to: String },

    /// The trader has no open trades.
    #[error("no open trades for {0:?}")]
    NoOpenTrades(Address),

    /// A specific trade lookup miss.
    #[error("trade not found for {trader:?} pair {pair_id} and index {index}")]
    TradeNotFound {
        trader: Address,
        pair_id: u64,
        index: u64,
    },

    /// The pair details were missing for the supplied id.
    #[error("no pair details found for pair ID: {0}")]
    PairNotFound(String),

    /// On-chain revert decoded into an Ostium custom error selector.
    #[error("on-chain revert: {0}")]
    OnChainRevert(String),

    /// Insufficient ETH to pay gas; suggestion: top up the wallet.
    #[error("insufficient ETH for gas: {0}")]
    InsufficientGas(String),

    /// USDC transfer exceeded balance.
    #[error("insufficient USDC balance")]
    InsufficientUsdc,

    /// Sufficient allowance not present (delegation mode).
    #[error("insufficient USDC allowance for {0:?}; delegated trader must approve the trading contract")]
    InsufficientAllowance(Address),

    /// Builder fee was set above the 0.5% maximum.
    #[error("builder fee too high: max 0.5 (0.5%)")]
    BuilderFeeTooHigh,

    /// Catch-all for transport / contract call errors that don't decode.
    #[error("contract call failed: {0}")]
    Contract(String),

    /// Numeric conversion failed (e.g. Decimal → U256).
    #[error("numeric conversion failed: {0}")]
    Conversion(String),

    /// The order_type string was unrecognised.
    #[error("invalid order type: {0}")]
    InvalidOrderType(String),
}

impl From<alloy::contract::Error> for OstiumError {
    fn from(e: alloy::contract::Error) -> Self {
        OstiumError::Contract(e.to_string())
    }
}
