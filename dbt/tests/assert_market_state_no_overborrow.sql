-- Contract invariant: a market cannot lend more than it holds.
-- Tolerance covers float64 rounding of decimal-normalised amounts.
select market_id, block_number, total_supply_assets, total_borrow_assets
from {{ ref('stg_morpho__market_state') }}
where total_borrow_assets > total_supply_assets * (1 + 1e-9)
