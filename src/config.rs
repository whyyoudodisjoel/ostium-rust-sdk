use alloy::primitives::{Address, address};
use serde::{Deserialize, Serialize};
use url::Url;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Contracts {
    pub usdc: Address,
    pub trading: Address,
    pub trading_storage: Address,
}

#[derive(Debug, Clone)]
pub struct NetworkConfig {
    pub graph_url: Url,
    pub is_testnet: bool,
    pub contracts: Contracts,
}

impl NetworkConfig {
    pub fn mainnet() -> NetworkConfig {
        NetworkConfig {
            graph_url: "https://api.subgraph.ormilabs.com/api/public/67a599d5-c8d2-4cc4-9c4d-2975a97bc5d8/subgraphs/ost-prod/live/gn".parse().unwrap(),
            contracts: Contracts {
                usdc: address!("0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
                trading: address!("0x6D0bA1f9996DBD8885827e1b2e8f6593e7702411"),
                trading_storage: address!("0xcCd5891083A8acD2074690F65d3024E7D13d66E7"),
            },
            is_testnet: false,
        }
    }

    pub fn testnet() -> NetworkConfig {
        NetworkConfig {
            graph_url: "https://api.subgraph.ormilabs.com/api/public/67a599d5-c8d2-4cc4-9c4d-2975a97bc5d8/subgraphs/ost-sep/live/gn".parse().unwrap(),
            contracts: Contracts {
                usdc: address!("0xe73B11Fb1e3eeEe8AF2a23079A4410Fe1B370548"),
                trading: address!("0x2A9B9c988393f46a2537B0ff11E98c2C15a95afe"),
                trading_storage: address!("0x0b9F5243B29938668c9Cfbd7557A389EC7Ef88b8"),
            },
            is_testnet: true,
        }
    }
}
