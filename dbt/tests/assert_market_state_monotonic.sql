-- Sampling invariant (docs/DATA.md, 3.2): block_ts strictly increasing per
-- market, and block order must agree with time order.
with ordered as (

    select
        market_id,
        block_number,
        block_ts,
        lag(block_ts) over (partition by market_id order by block_number) as prev_block_ts
    from {{ ref('stg_morpho__market_state') }}

)

select *
from ordered
where prev_block_ts is not null
    and block_ts <= prev_block_ts
