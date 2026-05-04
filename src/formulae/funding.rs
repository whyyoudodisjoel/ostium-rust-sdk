use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, MathematicalOps, RoundingStrategy};
use rust_decimal_macros::dec;

const RD: RoundingStrategy = RoundingStrategy::ToZero;

pub fn get_target_funding_rate(
    normalized_oi_delta: Decimal,
    hill_inflection_point: Decimal,
    max_funding_fee_per_block: Decimal,
    hill_pos_scale: Decimal,
    hill_neg_scale: Decimal,
) -> Decimal {
    let a = dec!(1.84);
    let n = 2u64;
    let k = dec!(0.16);
    let x = (a * normalized_oi_delta).round_dp_with_strategy(6, RD);
    let x2 = x.powi(n as i64).round_dp_with_strategy(18, RD);
    let hill = (x2 / (k + x2)).round_dp_with_strategy(18, RD);

    let target_fr = if normalized_oi_delta >= Decimal::ZERO {
        (hill_pos_scale * hill).round_dp_with_strategy(18, RD) + hill_inflection_point
    } else {
        (-hill_neg_scale * hill).round_dp_with_strategy(18, RD) + hill_inflection_point
    };
    let target_fr = target_fr.clamp(-Decimal::ONE, Decimal::ONE);

    (max_funding_fee_per_block * target_fr).round_dp_with_strategy(18, RD)
}

pub fn get_pending_acc_funding_fees(
    block_number: Decimal,
    last_update_block: Decimal,
    mut value_long: Decimal,
    mut value_short: Decimal,
    open_interest_usdc_long: Decimal,
    open_interest_usdc_short: Decimal,
    oi_cap: Decimal,
    max_funding_fee_per_block: Decimal,
    last_funding_rate: Decimal,
    hill_inflection_point: Decimal,
    hill_pos_scale: Decimal,
    hill_neg_scale: Decimal,
    spring_factor: Decimal,
    s_factor_upscale: Decimal,
    s_factor_down_scale_p: Decimal,
) -> (Decimal, Decimal, Decimal, Decimal) {
    let num_blocks = block_number - last_update_block;
    let open_interest_max = open_interest_usdc_long.max(open_interest_usdc_short);

    let denominator = oi_cap.max(open_interest_max).round_dp_with_strategy(6, RD);
    let norm_oi_delta = ((open_interest_usdc_long - open_interest_usdc_short)
        .round_dp_with_strategy(6, RD)
        / denominator)
        .round_dp_with_strategy(6, RD);

    let target_fr = get_target_funding_rate(
        norm_oi_delta,
        hill_inflection_point,
        max_funding_fee_per_block,
        hill_pos_scale,
        hill_neg_scale,
    );

    let hundred = Decimal::from(100);
    let s_factor = if (last_funding_rate * target_fr) >= Decimal::ZERO {
        if target_fr.abs() > last_funding_rate.abs() {
            spring_factor
        } else {
            (s_factor_down_scale_p * spring_factor) / hundred
        }
    } else {
        (s_factor_upscale * spring_factor) / hundred
    };

    let exp_input = -(s_factor * num_blocks);
    let exp_comp = exp_approx(exp_input);

    let term1 = (target_fr * num_blocks).round_dp_with_strategy(18, RD);
    let term2 = ((Decimal::ONE - exp_comp) * (last_funding_rate - target_fr) / s_factor)
        .round_dp_with_strategy(18, RD);
    let acc_funding_rate = term1 + term2;

    let fr = target_fr + ((last_funding_rate - target_fr) * exp_comp).round_dp_with_strategy(18, RD);

    if acc_funding_rate > Decimal::ZERO {
        if open_interest_usdc_long > Decimal::ZERO {
            value_long += acc_funding_rate;
            if open_interest_usdc_short > Decimal::ZERO {
                let short_adj = (acc_funding_rate * open_interest_usdc_long
                    / open_interest_usdc_short)
                    .round_dp_with_strategy(18, RD);
                value_short -= short_adj;
            }
        }
    } else if acc_funding_rate < Decimal::ZERO {
        if open_interest_usdc_short > Decimal::ZERO {
            value_short -= acc_funding_rate; // subtracting negative adds to value
            if open_interest_usdc_long > Decimal::ZERO {
                let long_adj = (acc_funding_rate * open_interest_usdc_short
                    / open_interest_usdc_long)
                    .round_dp_with_strategy(18, RD);
                value_long += long_adj;
            }
        }
    }

    (
        value_long.round_dp_with_strategy(18, RD),
        value_short.round_dp_with_strategy(18, RD),
        fr.round_dp_with_strategy(18, RD),
        target_fr.round_dp_with_strategy(18, RD),
    )
}

/// Padé-style + lookup-table exponential approximation matching the on-chain implementation.
pub fn exp_approx(val: Decimal) -> Decimal {
    if val.abs() < dec!(0.7932312589092019) {
        let three = Decimal::from(3);
        let n_tmp = val + three;
        let numerator = (n_tmp * n_tmp).round_dp_with_strategy(18, RD) + three;
        let d_tmp = val - three;
        let denominator = (d_tmp * d_tmp).round_dp_with_strategy(18, RD) + three;
        return (numerator / denominator).round_dp_with_strategy(18, RD);
    } else if val.abs() <= dec!(6.906) {
        let k_values = [
            dec!(1.648721),
            dec!(1.284025),
            dec!(1.133148),
            dec!(1.064494),
            dec!(1.031743),
            dec!(1.015748),
            dec!(1.007843),
            dec!(1.003915),
            dec!(1.001955),
            dec!(1.000977),
        ];

        let mut product = Decimal::ONE;
        let abs_val = val.abs();
        let integer_part = abs_val.round_dp_with_strategy(0, RD);
        let mut decimal_part = abs_val - integer_part;
        let two = Decimal::from(2);

        for k in k_values.iter() {
            decimal_part *= two;
            if decimal_part >= Decimal::ONE {
                product = (product * *k).round_dp_with_strategy(6, RD);
                decimal_part -= Decimal::ONE;
            }
            if decimal_part == Decimal::ZERO {
                break;
            }
        }

        let pow_val = integer_part.to_u64().unwrap_or(0);
        let multiplier = two.powi(pow_val as i64);

        product = product.round_dp_with_strategy(3, RD) * multiplier;

        let final_denominator = product.round_dp_with_strategy(18, RD);
        return (Decimal::ONE / final_denominator).round_dp_with_strategy(3, RD);
    } else {
        Decimal::ZERO
    }
}
