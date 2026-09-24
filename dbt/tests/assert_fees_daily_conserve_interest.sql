-- The day split neither creates nor loses interest: per market, daily fees
-- plus stuck interest add up to the interest of the covered intervals. It
-- fails if the day spine of mart_protocol_fees_daily misses a day, which
-- only an interval longer than a day could cause.
with daily as (

    select
        market_id,
        sum(fees_loan_units + stuck_interest_loan_units)    as daily_total
    from {{ ref('mart_protocol_fees_daily') }}
    group by 1

),

intervals as (

    select
        market_id,
        sum(interest)                                       as interval_total,
        max(greatest(abs(supply_assets_start), abs(supply_assets_end))) as scale
    from {{ ref('int_morpho__interest_intervals') }}
    where is_covered
    group by 1

)

select
    i.market_id,
    i.interval_total,
    d.daily_total
from intervals as i
left join daily as d
    on d.market_id = i.market_id
where d.daily_total is null
    or abs(d.daily_total - i.interval_total) > 1e-9 * greatest(i.scale, 1)
