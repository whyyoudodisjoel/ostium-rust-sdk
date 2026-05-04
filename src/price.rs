//! Price feed client for the Ostium metadata service.

use std::time::Duration;

use serde::{Deserialize, Serialize};

use crate::error::{OstiumError, Result};

const BASE_URL: &str = "https://metadata-backend.ostium.io";

/// Single price-feed entry returned by the metadata service.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PriceEntry {
    pub feed_id: Option<String>,
    pub bid: f64,
    pub mid: f64,
    pub ask: f64,
    pub is_market_open: bool,
    pub is_day_trading_closed: bool,
    pub seconds_to_toggle_is_day_trading_closed: i64,
    pub from: String,
    pub to: String,
    pub timestamp_seconds: i64,
}

/// Price-feed client.
pub struct Price {
    pub base_url: String,
    client: reqwest::Client,
}

impl Default for Price {
    fn default() -> Self {
        Self::new()
    }
}

impl Price {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("failed to build reqwest client");
        Self {
            base_url: BASE_URL.to_string(),
            client,
        }
    }

    /// Fetch the full set of latest prices.
    pub async fn get_latest_prices(&self) -> Result<Vec<PriceEntry>> {
        let url = format!("{}/PricePublish/latest-prices", self.base_url);
        let resp = self.client.get(&url).send().await?;
        if !resp.status().is_success() {
            return Err(OstiumError::SubgraphStatus(resp.status().as_u16()));
        }
        Ok(resp.json::<Vec<PriceEntry>>().await?)
    }

    /// Find the price entry for `from`/`to`, or [`OstiumError::PriceNotFound`].
    pub async fn get_latest_price(&self, from: &str, to: &str) -> Result<PriceEntry> {
        let prices = self.get_latest_prices().await?;
        prices
            .into_iter()
            .find(|p| p.from == from && p.to == to)
            .ok_or_else(|| OstiumError::PriceNotFound {
                from: from.to_string(),
                to: to.to_string(),
            })
    }

    /// `(mid, is_market_open, is_day_trading_closed)` shorthand.
    pub async fn get_price(&self, from: &str, to: &str) -> Result<(f64, bool, bool)> {
        tracing::debug!("getting price for {}/{}", from, to);
        let p = self.get_latest_price(from, to).await?;
        Ok((p.mid, p.is_market_open, p.is_day_trading_closed))
    }
}
