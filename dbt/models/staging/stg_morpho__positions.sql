select
    lower(market_id)                                            as market_id,
    lower(borrower)                                             as borrower,
    cast(block_number as {{ dbt.type_bigint() }})               as block_number,
    block_ts,
    borrow_shares,
    collateral,
    borrow_assets,
    ltv,
    health_factor
from {{ source('morpho_cache', 'positions') }}
