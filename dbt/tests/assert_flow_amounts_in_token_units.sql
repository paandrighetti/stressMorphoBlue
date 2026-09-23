-- Unit guard. Cache amounts are decimal-normalised (scripts/fetch_events.py
-- divides by 10 ** decimals). A single flow above 1e13 loan units cannot
-- exist for any asset on the roster (total USDC supply is about 6e10) and
-- signals raw integer units leaking into the cache.
select event_key, market_id, flow_type, amount_loan_units
from {{ ref('int_morpho__flow_events') }}
where abs(amount_loan_units) > 1e13
