//! On-chain Ostium client.

use std::str::FromStr;
use std::sync::LazyLock;

use alloy::network::{EthereumWallet, TransactionBuilder};
use alloy::primitives::aliases::U192;
use alloy::primitives::{Address, B256, Bytes, FixedBytes, U256, address, keccak256};
use alloy::providers::{DynProvider, Provider, ProviderBuilder};
use alloy::rpc::types::{TransactionReceipt, TransactionRequest};
use alloy::signers::local::PrivateKeySigner;
use alloy::sol_types::{SolCall, SolInterface};
use rust_decimal::Decimal;

use crate::contracts::trading::IOstiumTrading::{
    IOstiumTradingErrors, cancelOpenLimitOrderCall, closeTradeMarketCall,
    closeTradeMarketTimeoutCall, delegatedActionCall, openTradeCall, openTradeMarketTimeoutCall,
    removeCollateralCall, topUpCollateralCall, updateOpenLimitOrderCall, updateSlCall, updateTpCall,
};
use crate::contracts::trading::IOstiumTradingStorage::{BuilderFee, Trade};
use crate::contracts::trading_storage::IOstiumTradingStorage as IStorage;
use crate::contracts::usdc::IUSDC;
use crate::error::{OstiumError, Result};
use crate::subgraph::{OrderRecord, SubgraphClient, TradeRecord};
use crate::utils::{
    TradeParams, convert_to_scaled_integer, convert_to_scaled_integer_default, to_base_units,
};

/// `keccak256("PriceRequested(uint256,bytes32,uint256)")`. The orderId is the
/// indexed first parameter.
static PRICE_REQUESTED_SIG: LazyLock<FixedBytes<32>> =
    LazyLock::new(|| keccak256("PriceRequested(uint256,bytes32,uint256)".as_bytes()));

/// Order type for `openTrade`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum OpenOrderType {
    /// Execute immediately at the next price; honours `slippageP`.
    #[default]
    Market = 0,
    /// Resting limit order.
    Limit = 1,
    /// Resting stop order.
    Stop = 2,
}

/// Outcome of a trade-modifying call (open, close).
#[derive(Debug)]
pub struct TradeOutcome {
    pub receipt: TransactionReceipt,
    /// `orderId` extracted from the `PriceRequested` event, if present.
    pub order_id: Option<U256>,
}

#[derive(Debug)]
pub struct CloseMarketTimeoutOutcome {
    pub receipt: TransactionReceipt,
    pub order_id: U256,
    pub retry: bool,
}

#[derive(Debug)]
pub struct OpenMarketTimeoutOutcome {
    pub receipt: TransactionReceipt,
    pub order_id: U256,
}

/// Result of [`Ostium::track_order_and_trade`].
#[derive(Debug, Clone, Default)]
pub struct TrackedOrder {
    pub order: Option<OrderRecord>,
    pub trade: Option<TradeRecord>,
}

/// Decode a contract revert blob using the generated `IOstiumTradingErrors`
/// enum, falling back to common transport-level error patterns.
fn decode_revert(error_str: &str) -> OstiumError {
    if let Some(start) = error_str.find("0x") {
        let candidate: String = error_str[start..]
            .chars()
            .take_while(|c| c.is_ascii_hexdigit() || *c == 'x' || *c == 'X')
            .collect();
        if candidate.len() >= 10 {
            if let Ok(bytes) = alloy::hex::decode(candidate.trim_start_matches("0x")) {
                if let Ok(err) = IOstiumTradingErrors::abi_decode(&bytes) {
                    let sel = err.selector();
                    return OstiumError::OnChainRevert(format!(
                        "selector 0x{}",
                        alloy::hex::encode(sel)
                    ));
                }
            }
        }
    }

    if error_str.contains("insufficient funds for gas * price + value") {
        return OstiumError::InsufficientGas(error_str.to_string());
    }
    if error_str.contains("ERC20: transfer amount exceeds balance") {
        return OstiumError::InsufficientUsdc;
    }
    OstiumError::Contract(error_str.to_string())
}

/// On-chain client for the Ostium trading contracts on Arbitrum.
pub struct Ostium {
    pub provider: DynProvider,
    pub usdc_address: Address,
    pub ostium_trading_storage_address: Address,
    pub ostium_trading_address: Address,
    pub use_delegation: bool,
    pub slippage_percentage: Decimal,
    signer: Option<PrivateKeySigner>,
    wallet_address: Option<Address>,
}

impl Ostium {
    /// Construct a client. Pass `signer = Some(_)` to enable write methods.
    pub fn new(
        provider: DynProvider,
        usdc_address: Address,
        ostium_trading_storage_address: Address,
        ostium_trading_address: Address,
        signer: Option<PrivateKeySigner>,
        use_delegation: bool,
    ) -> Self {
        let wallet_address = signer.as_ref().map(|s| s.address());
        Self {
            provider,
            usdc_address,
            ostium_trading_storage_address,
            ostium_trading_address,
            use_delegation,
            slippage_percentage: Decimal::TWO,
            signer,
            wallet_address,
        }
    }

    pub fn set_slippage_percentage(&mut self, slippage_percentage: Decimal) {
        self.slippage_percentage = slippage_percentage;
    }

    pub fn slippage_percentage(&self) -> Decimal {
        self.slippage_percentage
    }

    pub fn public_address(&self) -> Result<Address> {
        self.wallet_address.ok_or(OstiumError::MissingPrivateKey)
    }

    fn signer(&self) -> Result<&PrivateKeySigner> {
        self.signer.as_ref().ok_or(OstiumError::MissingPrivateKey)
    }

    fn from_address(&self) -> Result<Address> {
        self.wallet_address.ok_or(OstiumError::MissingPrivateKey)
    }

    pub async fn block_number(&self) -> Result<u64> {
        self.provider
            .get_block_number()
            .await
            .map_err(|e| OstiumError::Contract(e.to_string()))
    }

    pub async fn nonce(&self, address: Address) -> Result<u64> {
        self.provider
            .get_transaction_count(address)
            .await
            .map_err(|e| OstiumError::Contract(e.to_string()))
    }

    fn signer_provider(&self) -> Result<DynProvider> {
        let signer = self.signer()?.clone();
        let wallet = EthereumWallet::from(signer);
        Ok(ProviderBuilder::new()
            .wallet(wallet)
            .connect_provider(self.provider.clone())
            .erased())
    }

    async fn send_call(
        &self,
        to: Address,
        data: Bytes,
        from: Address,
    ) -> Result<TransactionReceipt> {
        let provider = self.signer_provider()?;
        let tx = TransactionRequest::default()
            .with_from(from)
            .with_to(to)
            .with_input(data);

        let pending = provider
            .send_transaction(tx)
            .await
            .map_err(|e| decode_revert(&e.to_string()))?;
        pending
            .get_receipt()
            .await
            .map_err(|e| decode_revert(&e.to_string()))
    }

    async fn approve_if_needed(
        &self,
        from: Address,
        collateral: U256,
        trader_address: Option<Address>,
    ) -> Result<()> {
        let owner_addr = if self.use_delegation && trader_address.is_some() {
            trader_address.unwrap()
        } else {
            from
        };

        let usdc = IUSDC::new(self.usdc_address, &self.provider);
        let allowance = usdc
            .allowance(owner_addr, self.ostium_trading_storage_address)
            .call()
            .await?;

        if allowance < collateral {
            if !self.use_delegation {
                let approve_call = IUSDC::approveCall {
                    spender: self.ostium_trading_storage_address,
                    amount: U256::from(1_000_000u64) * U256::from(1_000_000u64),
                };
                let data = Bytes::from(approve_call.abi_encode());
                let receipt = self.send_call(self.usdc_address, data, from).await?;
                tracing::debug!("approval tx: {:?}", receipt.transaction_hash);
            } else {
                return Err(OstiumError::InsufficientAllowance(owner_addr));
            }
        }
        Ok(())
    }

    fn extract_order_id(receipt: &TransactionReceipt) -> Option<U256> {
        for log in receipt.inner.logs() {
            let topics = log.topics();
            if topics.len() > 1 && topics[0] == *PRICE_REQUESTED_SIG {
                let bytes: B256 = topics[1];
                return Some(U256::from_be_bytes::<32>(bytes.0));
            }
        }
        None
    }

    fn dec_to_u192(value: Decimal) -> Result<U192> {
        let s = value
            .round_dp_with_strategy(0, rust_decimal::RoundingStrategy::ToZero)
            .to_string();
        U192::from_str(&s).map_err(|e| OstiumError::Conversion(e.to_string()))
    }

    fn dec_to_u256(value: Decimal) -> Result<U256> {
        let s = value
            .round_dp_with_strategy(0, rust_decimal::RoundingStrategy::ToZero)
            .to_string();
        U256::from_str(&s).map_err(|e| OstiumError::Conversion(e.to_string()))
    }

    /// Open a new trade.
    pub async fn open_trade(
        &self,
        params: &TradeParams,
        at_price: Decimal,
    ) -> Result<TradeOutcome> {
        tracing::debug!("performing trade with params: {:?}", params);
        let from = self.from_address()?;

        let amount = U256::from(to_base_units(params.collateral, 6));

        self.approve_if_needed(from, amount, params.trader_address)
            .await?;

        let (tp_price, sl_price) = params.tp_sl_prices();

        let collateral_scaled = convert_to_scaled_integer(params.collateral, 5, 6);
        let open_price_scaled = convert_to_scaled_integer_default(at_price);
        let tp_scaled = convert_to_scaled_integer_default(tp_price);
        let sl_scaled = convert_to_scaled_integer_default(sl_price);

        let trade = Trade {
            collateral: Self::dec_to_u256(collateral_scaled)?,
            openPrice: Self::dec_to_u192(open_price_scaled)?,
            tp: Self::dec_to_u192(tp_scaled)?,
            sl: Self::dec_to_u192(sl_scaled)?,
            trader: from,
            leverage: to_base_units(params.leverage, 2) as u32,
            pairIndex: params.asset_type,
            index: 0,
            buy: params.direction,
            isDayTrade: params.is_day_trade,
        };

        let slippage = if params.order_type == OpenOrderType::Market {
            U256::from(to_base_units(self.slippage_percentage * Decimal::from(100), 0))
        } else {
            U256::ZERO
        };

        let mut builder_fee = BuilderFee {
            builder: address!("0x0000000000000000000000000000000000000000"),
            builderFee: 0,
        };

        if let (Some(addr), Some(fee)) = (params.builder_address, params.builder_fee) {
            if fee > Decimal::new(5, 1) {
                return Err(OstiumError::BuilderFeeTooHigh);
            }
            let fee_u: u32 = convert_to_scaled_integer(fee, 4, 6)
                .to_string()
                .parse()
                .map_err(|e: std::num::ParseIntError| OstiumError::Conversion(e.to_string()))?;
            builder_fee = BuilderFee {
                builder: addr,
                builderFee: fee_u,
            };
        }

        let open_call = openTradeCall {
            t: trade,
            bf: builder_fee,
            orderType: params.order_type as u8,
            slippageP: slippage,
        };
        let inner = open_call.abi_encode();

        let data = self.maybe_delegate(inner, params.trader_address);

        let receipt = self.send_call(self.ostium_trading_address, data, from).await?;
        let order_id = Self::extract_order_id(&receipt);
        if let Some(id) = order_id {
            tracing::debug!("PriceRequested orderId: {}", id);
        }

        Ok(TradeOutcome { receipt, order_id })
    }

    /// Wrap `inner_call_data` in a `delegatedAction` if delegation is on and a
    /// `trader_address` was supplied.
    fn maybe_delegate(&self, inner: Vec<u8>, trader_address: Option<Address>) -> Bytes {
        if self.use_delegation && trader_address.is_some() {
            let trader = trader_address.unwrap();
            tracing::debug!("delegating to {:?}", trader);
            let delegated = delegatedActionCall {
                trader,
                call_data: Bytes::from(inner),
            };
            Bytes::from(delegated.abi_encode())
        } else {
            Bytes::from(inner)
        }
    }

    pub async fn cancel_limit_order(
        &self,
        pair_id: u16,
        trade_index: u8,
        trader_address: Option<Address>,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let inner = cancelOpenLimitOrderCall {
            pairIndex: pair_id,
            index: trade_index,
        }
        .abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        self.send_call(self.ostium_trading_address, data, from).await
    }

    pub async fn close_trade(
        &self,
        pair_id: u16,
        trade_index: u8,
        market_price: Decimal,
        close_percentage: Decimal,
        trader_address: Option<Address>,
    ) -> Result<TradeOutcome> {
        tracing::debug!("closing trade pair {} index {}", pair_id, trade_index);
        let from = self.from_address()?;

        let close_pct_u = to_base_units(close_percentage, 2) as u16;
        let market_price_u = Self::dec_to_u192(convert_to_scaled_integer_default(market_price))?;
        let slippage_u =
            to_base_units(self.slippage_percentage * Decimal::from(100), 0) as u32;

        let inner = closeTradeMarketCall {
            pairIndex: pair_id,
            index: trade_index,
            closePercentage: close_pct_u,
            marketPrice: market_price_u,
            slippageP: slippage_u,
        }
        .abi_encode();

        let data = self.maybe_delegate(inner, trader_address);
        let receipt = self.send_call(self.ostium_trading_address, data, from).await?;
        let order_id = Self::extract_order_id(&receipt);
        Ok(TradeOutcome { receipt, order_id })
    }

    pub async fn close_market_timeout(
        &self,
        order_id: U256,
        retry: bool,
        trader_address: Option<Address>,
    ) -> Result<CloseMarketTimeoutOutcome> {
        let from = self.from_address()?;
        let inner = closeTradeMarketTimeoutCall {
            _order: order_id,
            retry,
        }
        .abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        let receipt = self.send_call(self.ostium_trading_address, data, from).await?;
        Ok(CloseMarketTimeoutOutcome {
            receipt,
            order_id,
            retry,
        })
    }

    pub async fn open_market_timeout(
        &self,
        order_id: U256,
        trader_address: Option<Address>,
    ) -> Result<OpenMarketTimeoutOutcome> {
        let from = self.from_address()?;
        let inner = openTradeMarketTimeoutCall { _order: order_id }.abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        let receipt = self.send_call(self.ostium_trading_address, data, from).await?;
        Ok(OpenMarketTimeoutOutcome { receipt, order_id })
    }

    pub async fn remove_collateral(
        &self,
        pair_id: u16,
        trade_index: u8,
        remove_amount: Decimal,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let amount = U256::from(to_base_units(remove_amount, 6));
        let data = Bytes::from(
            removeCollateralCall {
                pairIndex: pair_id,
                index: trade_index,
                removeAmount: amount,
            }
            .abi_encode(),
        );
        self.send_call(self.ostium_trading_address, data, from).await
    }

    pub async fn add_collateral(
        &self,
        pair_id: u16,
        index: u8,
        collateral: Decimal,
        trader_address: Option<Address>,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let amount = U256::from(to_base_units(collateral, 6));
        self.approve_if_needed(from, amount, trader_address).await?;

        let inner = topUpCollateralCall {
            pairIndex: pair_id,
            index,
            topUpAmount: amount,
        }
        .abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        self.send_call(self.ostium_trading_address, data, from).await
    }

    pub async fn update_tp(
        &self,
        pair_id: u16,
        trade_index: u8,
        tp_price: Decimal,
        trader_address: Option<Address>,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let tp_value = U192::from(to_base_units(tp_price, 18));
        let inner = updateTpCall {
            pairIndex: pair_id,
            index: trade_index,
            newTp: tp_value,
        }
        .abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        self.send_call(self.ostium_trading_address, data, from).await
    }

    pub async fn update_sl(
        &self,
        pair_id: u16,
        index: u8,
        sl: Decimal,
        trader_address: Option<Address>,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let sl_value = U192::from(to_base_units(sl, 18));
        let inner = updateSlCall {
            pairIndex: pair_id,
            index,
            newSl: sl_value,
        }
        .abi_encode();
        let data = self.maybe_delegate(inner, trader_address);
        self.send_call(self.ostium_trading_address, data, from).await
    }

    /// Transfer USDC from this account to `to`.
    pub async fn withdraw(
        &self,
        amount: Decimal,
        to: Address,
    ) -> Result<TransactionReceipt> {
        let from = self.from_address()?;
        let amount_u = U256::from(to_base_units(amount, 6));
        let data = Bytes::from(
            IUSDC::transferCall {
                to,
                amount: amount_u,
            }
            .abi_encode(),
        );
        self.send_call(self.usdc_address, data, from).await
    }

    /// Update an existing limit order. `signer` controls the order; pass `None`
    /// to use the SDK's signer.
    pub async fn update_limit_order(
        &self,
        pair_id: u16,
        index: u8,
        price: Option<Decimal>,
        tp: Option<Decimal>,
        sl: Option<Decimal>,
        signer: Option<&PrivateKeySigner>,
    ) -> Result<TransactionReceipt> {
        let signer = signer
            .cloned()
            .or_else(|| self.signer.clone())
            .ok_or(OstiumError::MissingPrivateKey)?;
        let from = signer.address();

        let storage = IStorage::new(self.ostium_trading_storage_address, &self.provider);
        let existing_order = storage
            .getOpenLimitOrder(from, pair_id, index)
            .call()
            .await?;

        tracing::debug!(
            "existing_order targetPrice={} tp={} sl={} collateral={}",
            existing_order.targetPrice,
            existing_order.tp,
            existing_order.sl,
            existing_order.collateral
        );

        let to_u192 = |opt: Option<Decimal>, fallback: U192| -> Result<U192> {
            match opt {
                Some(v) => Self::dec_to_u192(convert_to_scaled_integer_default(v)),
                None => Ok(fallback),
            }
        };

        let price_value = to_u192(price, existing_order.targetPrice)?;
        let tp_value = to_u192(tp, existing_order.tp)?;
        let sl_value = to_u192(sl, existing_order.sl)?;

        let data = Bytes::from(
            updateOpenLimitOrderCall {
                pairIndex: pair_id,
                index,
                price: price_value,
                tp: tp_value,
                sl: sl_value,
            }
            .abi_encode(),
        );

        let wallet = EthereumWallet::from(signer);
        let provider = ProviderBuilder::new()
            .wallet(wallet)
            .connect_provider(self.provider.clone())
            .erased();
        let tx = TransactionRequest::default()
            .with_from(from)
            .with_to(self.ostium_trading_address)
            .with_input(data);

        let pending = provider
            .send_transaction(tx)
            .await
            .map_err(|e| decode_revert(&e.to_string()))?;
        pending
            .get_receipt()
            .await
            .map_err(|e| decode_revert(&e.to_string()))
    }

    /// Poll the subgraph until an order is no longer pending, then fetch its
    /// resulting trade.
    pub async fn track_order_and_trade(
        &self,
        subgraph_client: &SubgraphClient,
        order_id: U256,
        polling_interval: std::time::Duration,
        max_attempts: u32,
    ) -> Result<TrackedOrder> {
        tracing::debug!("tracking order {}", order_id);

        for attempt in 0..max_attempts {
            let order_opt = subgraph_client
                .get_order_by_id(order_id.to_string())
                .await?;

            let Some(order) = order_opt else {
                tracing::debug!(
                    "order {} not found yet (attempt {}/{})",
                    order_id,
                    attempt + 1,
                    max_attempts
                );
                tokio::time::sleep(polling_interval).await;
                continue;
            };

            if order.is_pending {
                tracing::debug!(
                    "order {} pending (attempt {}/{})",
                    order_id,
                    attempt + 1,
                    max_attempts
                );
                tokio::time::sleep(polling_interval).await;
                continue;
            }

            if order.is_cancelled {
                tracing::debug!(
                    "order {} cancelled: {:?}",
                    order_id,
                    order.cancel_reason
                );
                return Ok(TrackedOrder {
                    order: Some(order),
                    trade: None,
                });
            }

            if !order.trade_id.is_empty() {
                let trade = subgraph_client.get_trade_by_id(order.trade_id.clone()).await?;
                if let Some(trade) = trade {
                    if order.order_action == "Close" && trade.is_open {
                        tokio::time::sleep(polling_interval).await;
                        continue;
                    }
                    return Ok(TrackedOrder {
                        order: Some(order),
                        trade: Some(trade),
                    });
                }
            }

            return Ok(TrackedOrder {
                order: Some(order),
                trade: None,
            });
        }

        let order_opt = subgraph_client
            .get_order_by_id(order_id.to_string())
            .await?;
        Ok(TrackedOrder {
            order: order_opt,
            trade: None,
        })
    }
}
