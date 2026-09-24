-- Grain of mart_protocol_fees_daily: one row per UTC day and market.
select
    day,
    market_id,
    count(*) as n_rows
from {{ ref('mart_protocol_fees_daily') }}
group by 1, 2
having count(*) > 1
