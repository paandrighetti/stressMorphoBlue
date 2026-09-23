select
    lower(market_id)                                            as market_id,
    cast(block_number as {{ dbt.type_bigint() }})               as block_number,
    block_ts,
    price                                                       as price_collateral_per_loan,
    cast(price_decimals_raw as {{ dbt.type_int() }})            as price_decimals_raw,
    oracle_kind,
    cast(staleness_blocks as {{ dbt.type_int() }})              as staleness_blocks
from {{ source('morpho_cache', 'oracle_prices') }}
