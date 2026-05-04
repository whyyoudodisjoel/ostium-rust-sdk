//! Typed GraphQL client for the Ostium subgraph (built on `graphql-client`).
//!
//! Each query is a `.graphql` file under `queries/`; `graphql-client`'s derive
//! macro turns each into a typed module. Numeric scalars (`BigInt` /
//! `BigDecimal`) come over the wire as JSON strings; use [`DecExt::dec`]
//! / [`DecExt::dec_opt`] to parse them into [`rust_decimal::Decimal`].

use std::time::Duration;

use graphql_client::{GraphQLQuery, QueryBody, Response};
use rust_decimal::Decimal;
use serde::Serialize;
use serde::de::DeserializeOwned;

use crate::error::{OstiumError, Result};

pub(crate) mod generated;

// Re-export the generated per-query types under clean names.
pub use generated::get_open_trades::GetOpenTradesTrades as OpenTrade;
pub use generated::get_open_trades::GetOpenTradesTradesPair as OpenTradePair;
pub use generated::get_order_by_id::GetOrderByIdOrders as OrderRecord;
pub use generated::get_order_by_id::GetOrderByIdOrdersPair as OrderRecordPair;
pub use generated::get_orders::GetOrdersLimits as LimitOrder;
pub use generated::get_orders::GetOrdersLimitsPair as LimitOrderPair;
pub use generated::get_pair_details::GetPairDetailsPair as Pair;
pub use generated::get_pair_details::GetPairDetailsPairFee as PairFee;
pub use generated::get_pair_details::GetPairDetailsPairGroup as PairGroup;
pub use generated::get_pairs::GetPairsPairs as PairListEntry;
pub use generated::get_recent_history::GetRecentHistoryOrders as HistoryOrder;
pub use generated::get_recent_history::GetRecentHistoryOrdersPair as HistoryOrderPair;
pub use generated::get_trade_by_id::GetTradeByIdTrades as TradeRecord;
pub use generated::get_trade_by_id::GetTradeByIdTradesPair as TradeRecordPair;

/// Convenience extension trait for parsing wire-format strings into
/// [`Decimal`]. The subgraph encodes every `BigInt` and `BigDecimal` field
/// as a JSON string; the generated bindings expose them as `String` /
/// `Option<String>`.
pub trait DecExt {
    fn dec(&self) -> Decimal;
}

impl DecExt for String {
    fn dec(&self) -> Decimal {
        self.parse().unwrap_or(Decimal::ZERO)
    }
}

impl DecExt for str {
    fn dec(&self) -> Decimal {
        self.parse().unwrap_or(Decimal::ZERO)
    }
}

/// Companion for `Option<String>` since many fields are nullable in the schema.
pub trait DecOptExt {
    fn dec_opt(&self) -> Option<Decimal>;
}

impl DecOptExt for Option<String> {
    fn dec_opt(&self) -> Option<Decimal> {
        self.as_deref().and_then(|s| s.parse().ok())
    }
}

/// Subgraph client.
pub struct SubgraphClient {
    pub url: String,
    client: reqwest::Client,
}

impl SubgraphClient {
    pub fn new(url: impl Into<String>) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(60))
            .build()
            .expect("failed to build reqwest client");
        Self {
            url: url.into(),
            client,
        }
    }

    /// Run any [`GraphQLQuery`] and unwrap its `data` payload.
    async fn run<Q>(&self, variables: Q::Variables) -> Result<Q::ResponseData>
    where
        Q: GraphQLQuery,
        Q::Variables: Serialize,
        Q::ResponseData: DeserializeOwned,
    {
        let body: QueryBody<Q::Variables> = Q::build_query(variables);
        let resp: Response<Q::ResponseData> = self
            .client
            .post(&self.url)
            .json(&body)
            .send()
            .await?
            .error_for_status()
            .map_err(OstiumError::Http)?
            .json()
            .await?;

        if let Some(errors) = resp.errors {
            if !errors.is_empty() {
                return Err(OstiumError::SubgraphErrors(format!("{:?}", errors)));
            }
        }

        resp.data.ok_or(OstiumError::SubgraphMissingField("data"))
    }

    pub async fn get_pairs(&self) -> Result<Vec<PairListEntry>> {
        tracing::debug!("fetching pairs");
        let data = self
            .run::<generated::GetPairs>(generated::get_pairs::Variables {})
            .await?;
        Ok(data.pairs)
    }

    pub async fn get_pair_details(&self, pair_id: impl ToString) -> Result<Pair> {
        let id = pair_id.to_string();
        let vars = generated::get_pair_details::Variables { pair_id: id.clone() };
        let data = self.run::<generated::GetPairDetails>(vars).await?;
        data.pair.ok_or(OstiumError::PairNotFound(id))
    }

    pub async fn get_liq_margin_threshold_p(&self) -> Result<Decimal> {
        let data = self
            .run::<generated::GetLiqMarginThreshold>(
                generated::get_liq_margin_threshold::Variables {},
            )
            .await?;
        data.meta_datas
            .first()
            .ok_or(OstiumError::SubgraphMissingField("metaDatas[0]"))?
            .liq_margin_threshold_p
            .dec_opt()
            .ok_or(OstiumError::SubgraphMissingField("liqMarginThresholdP"))
    }

    pub async fn get_open_trades(&self, address: &str) -> Result<Vec<OpenTrade>> {
        let vars = generated::get_open_trades::Variables {
            trader: address.to_string(),
        };
        Ok(self.run::<generated::GetOpenTrades>(vars).await?.trades)
    }

    pub async fn get_orders(&self, trader: &str) -> Result<Vec<LimitOrder>> {
        let vars = generated::get_orders::Variables {
            trader: trader.to_string(),
        };
        Ok(self.run::<generated::GetOrders>(vars).await?.limits)
    }

    pub async fn get_recent_history(
        &self,
        trader: &str,
        last_n_orders: i64,
    ) -> Result<Vec<HistoryOrder>> {
        let vars = generated::get_recent_history::Variables {
            trader: Some(trader.to_string()),
            last_n_orders: Some(last_n_orders),
        };
        let mut orders = self.run::<generated::GetRecentHistory>(vars).await?.orders;
        orders.reverse();
        Ok(orders)
    }

    pub async fn get_order_by_id(&self, order_id: impl ToString) -> Result<Option<OrderRecord>> {
        let vars = generated::get_order_by_id::Variables {
            order_id: order_id.to_string(),
        };
        Ok(self
            .run::<generated::GetOrderById>(vars)
            .await?
            .orders
            .into_iter()
            .next())
    }

    pub async fn get_trade_by_id(&self, trade_id: impl ToString) -> Result<Option<TradeRecord>> {
        let vars = generated::get_trade_by_id::Variables {
            trade_id: trade_id.to_string(),
        };
        Ok(self
            .run::<generated::GetTradeById>(vars)
            .await?
            .trades
            .into_iter()
            .next())
    }
}
