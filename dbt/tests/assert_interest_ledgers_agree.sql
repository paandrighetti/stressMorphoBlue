-- The borrow and the supply ledgers give the same interest on every covered
-- interval (int_morpho__interest_intervals). A missing or duplicated flow
-- event moves one ledger and not the other. The check cannot see errors that
-- move both by the same amount: a supply and a borrow of equal size both
-- missing or both duplicated, the same for a withdrawal and a repayment, or a
-- wrong bad-debt amount, which enters both ledgers. Tolerance: float64
-- rounding of decimal-normalised amounts, 1e-9 of the supply.
select
    market_id,
    block_start,
    block_end,
    interest,
    interest_supply_ledger
from {{ ref('int_morpho__interest_intervals') }}
where is_covered
    and abs(interest - interest_supply_ledger)
        > 1e-9 * greatest(abs(supply_assets_start), abs(supply_assets_end), 1)
