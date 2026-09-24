-- Morpho Blue borrow rates are never negative, so the interest booked over a
-- covered interval cannot be negative beyond float64 rounding.
select
    market_id,
    block_start,
    block_end,
    interest
from {{ ref('int_morpho__interest_intervals') }}
where is_covered
    and interest < -1e-9 * greatest(abs(borrow_assets_start), abs(borrow_assets_end), 1)
