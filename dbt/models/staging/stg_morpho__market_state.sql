select
    lower(market_id)                                            as market_id,
    cast(block_number as {{ dbt.type_bigint() }})               as block_number,
    block_ts,
    total_supply_assets,
    total_supply_shares,
    total_borrow_assets,
    total_borrow_shares,
    total_collateral,
    cast(last_update as {{ dbt.type_bigint() }})                as last_update_block,
    fee,
    total_borrow_assets / nullif(total_supply_assets, 0)        as utilization
from {{ source('morpho_cache', 'market_state') }}
