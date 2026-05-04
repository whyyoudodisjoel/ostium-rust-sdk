use rust_decimal::Decimal;
use rust_decimal_macros::dec;

pub const CHAIN_ID_ARB_MAINNET: u64 = 42161;
pub const CHAIN_ID_ARB_TESTNET: u64 = 421614;

pub const MAX_PROFIT_P: Decimal = dec!(900);
pub const MAX_STOP_LOSS_P: u32 = 85;
pub const MIN_LOSS_P: Decimal = dec!(-100);

pub const PRECISION_2: Decimal = dec!(100);
pub const PRECISION_6: Decimal = dec!(1_000_000);
pub const PRECISION_9: Decimal = dec!(1_000_000_000);
pub const PRECISION_12: Decimal = dec!(1_000_000_000_000);
pub const PRECISION_16: Decimal = dec!(10_000_000_000_000_000);
pub const PRECISION_18: Decimal = dec!(1_000_000_000_000_000_000);

pub const QUANTIZATION_6: Decimal = dec!(0.000001);
// rust_decimal max scale is 28; PRECISION_18's reciprocal needs scale 18.
pub const QUANTIZATION_18: Decimal = dec!(0.000000000000000001);

pub const LIQ_THRESHOLD_PL: u32 = 90;
