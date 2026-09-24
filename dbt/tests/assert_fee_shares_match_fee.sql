-- Revenue check. The fee shares minted to the fee recipient (supply share
-- ledger) must be worth interest * fee. They are valued at the share price of
-- the end of the interval, which differs a little from the price at minting
-- (later interest raises it, bad debt lowers it), hence 1 % of relative
-- tolerance on top of float64 rounding. Intervals where the fee changed are
-- skipped: setFee books the interest due at the old fee first.
select
    market_id,
    block_start,
    block_end,
    revenue,
    fee_shares_value_end
from {{ ref('int_morpho__interest_intervals') }}
where is_covered
    and fee_start = fee_end
    and abs(fee_shares_value_end - revenue)
        > 0.01 * abs(revenue) + 1e-9 * greatest(abs(supply_assets_start), abs(supply_assets_end), 1)
