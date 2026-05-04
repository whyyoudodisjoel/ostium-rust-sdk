# isocline-ostium-rust-sdk

Rust SDK for the [Ostium](https://ostium.io) decentralized perpetual trading platform on Arbitrum.

Provides:

- **On-chain client** for opening/closing trades, managing positions, and approving USDC (via `OstiumClient`).
- **GraphQL subgraph client** returning typed responses (via `SubgraphClient`).
- **REST price-feed client** (via `Price`).
- **Pure formula helpers** for funding rate, PnL, liquidation price, etc.

## Quick start

```rust,no_run
use isocline_ostium_rust_sdk::{OstiumSDK, Network};

#[tokio::main]
async fn main() -> Result<(), isocline_ostium_rust_sdk::OstiumError> {
    let sdk = OstiumSDK::builder()
        .network(Network::Mainnet)
        .rpc_url("https://arb1.arbitrum.io/rpc".to_string())
        .build()
        .await?;

    let pairs = sdk.get_formatted_pairs_details(false).await?;
    println!("{} pairs", pairs.len());
    Ok(())
}
```

## License

Dual-licensed under MIT or Apache-2.0.
