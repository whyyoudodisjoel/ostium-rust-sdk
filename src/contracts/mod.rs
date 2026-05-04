//! Alloy `sol!`-generated bindings for every Ostium contract.
//!
//! Each submodule wraps one ABI from `abis/*.json` and exposes the full
//! typed surface area: calls, return values, events, and custom errors.

pub mod faucet_testnet;
pub mod pairs_info;
pub mod pairs_storage;
pub mod trading;
pub mod trading_storage;
pub mod usdc;
pub mod vault;
