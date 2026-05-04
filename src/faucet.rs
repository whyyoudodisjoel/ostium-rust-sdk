//! Testnet USDC faucet client.

use std::time::{SystemTime, UNIX_EPOCH};

use alloy::network::{EthereumWallet, TransactionBuilder};
use alloy::primitives::{Address, Bytes, U256, address};
use alloy::providers::{DynProvider, Provider, ProviderBuilder};
use alloy::rpc::types::{TransactionReceipt, TransactionRequest};
use alloy::signers::local::PrivateKeySigner;
use alloy::sol_types::SolCall;

use crate::contracts::faucet_testnet::IOstiumFaucetTestnet::{self, requestTokensCall};
use crate::error::{OstiumError, Result};

/// Hardcoded testnet faucet contract address (Arbitrum Sepolia).
pub const FAUCET_ADDRESS: Address = address!("0x6830C550814105d8B27bDAEC0DB391cAa7B967c8");

/// Testnet faucet client for receiving USDC.
pub struct Faucet {
    provider: DynProvider,
    signer: Option<PrivateKeySigner>,
}

impl Faucet {
    pub fn new(provider: DynProvider, signer: Option<PrivateKeySigner>) -> Self {
        Self { provider, signer }
    }

    fn signer(&self) -> Result<&PrivateKeySigner> {
        self.signer.as_ref().ok_or(OstiumError::MissingPrivateKey)
    }

    fn signer_provider(&self) -> Result<DynProvider> {
        let signer = self.signer()?.clone();
        let wallet = EthereumWallet::from(signer);
        Ok(ProviderBuilder::new()
            .wallet(wallet)
            .connect_provider(self.provider.clone())
            .erased())
    }

    /// Request testnet USDC tokens from the faucet.
    pub async fn request_tokens(&self) -> Result<TransactionReceipt> {
        let signer = self.signer()?;
        let from = signer.address();
        tracing::debug!("requesting tokens from faucet");

        let data = Bytes::from(requestTokensCall {}.abi_encode());
        let tx = TransactionRequest::default()
            .with_from(from)
            .with_to(FAUCET_ADDRESS)
            .with_input(data)
            .with_gas_limit(300_000);

        let provider = self.signer_provider()?;
        let pending = provider
            .send_transaction(tx)
            .await
            .map_err(|e| {
                let msg = e.to_string();
                if msg.contains("NotAllowed") {
                    OstiumError::Contract("faucet says NotAllowed (already claimed too recently)".to_string())
                } else if msg.contains("NotWhitelisted") {
                    OstiumError::Contract("faucet says NotWhitelisted".to_string())
                } else {
                    OstiumError::Contract(msg)
                }
            })?;
        pending
            .get_receipt()
            .await
            .map_err(|e| OstiumError::Contract(e.to_string()))
    }

    /// Check whether the given address may request tokens right now.
    pub async fn can_request_tokens(&self, address: Address) -> Result<bool> {
        let next = self.next_request_time(address).await?;
        let now = U256::from(now_unix_secs());
        Ok(now >= next)
    }

    /// Amount of tokens dispensed by a successful `request_tokens` call.
    pub async fn token_amount(&self) -> Result<U256> {
        let faucet = IOstiumFaucetTestnet::new(FAUCET_ADDRESS, &self.provider);
        Ok(faucet.tokenAmount().call().await?)
    }

    /// Earliest unix timestamp at which `address` may request tokens again.
    pub async fn next_request_time(&self, address: Address) -> Result<U256> {
        let faucet = IOstiumFaucetTestnet::new(FAUCET_ADDRESS, &self.provider);
        Ok(faucet.nextRequestTime(address).call().await?)
    }
}

fn now_unix_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
