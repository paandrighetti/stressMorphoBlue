{#- Latest cached state per market at or before the publication block
    (var state_block, docs/evaluation_manifest.json). This is the only
    balance figure the SQL layer exposes, and it comes from eth_call reads. -#}
with ranked as (

    select
        s.*,
        row_number() over (
            partition by s.market_id
            order by s.block_number desc
        )                                       as recency_rank
    from {{ ref('stg_morpho__market_state') }} as s
    where s.block_number <= {{ var('state_block') }}

)

select
    market_id,
    block_number                                as cached_state_block,
    block_ts                                    as cached_state_block_ts,
    total_supply_assets,
    total_supply_shares,
    total_borrow_assets,
    total_borrow_shares,
    total_collateral,
    fee,
    utilization
from ranked
where recency_rank = 1
