{#- Daily fees of Morpho Blue per market, in Token Terminal's terms (docs/FEES.md):
      fees              interest paid by borrowers
      supply_side_fees  the part paid to suppliers (fees - revenue)
      revenue           the part the protocol keeps (interest * market fee)
    Interest comes from the covered intervals of int_morpho__interest_intervals
    and is spread over UTC days pro rata to the seconds of each interval that
    fall in the day. Interest booked while a market is pinned at full
    utilization (is_stuck) is reported in its own column and left out of fees.
    The liquidation incentive (collateral seized above the debt repaid) is
    reported apart as well, by choice of scope: add it to fees for DefiLlama's
    definition.
    Amounts are in the market's loan asset: never sum them across loan assets. -#}
with intervals as (

    select
        market_id,
        ts_start,
        ts_end,
        interest,
        revenue,
        is_stuck,
        {{ dbt.datediff('ts_start', 'ts_end', 'second') }}         as interval_seconds
    from {{ ref('int_morpho__interest_intervals') }}
    where is_covered

),

-- Every UTC day that an interval starts or ends on, over all markets.
days as (

    select
        day_start,
        {{ timestamp_add_days('day_start', 1) }}                   as day_end
    from (
        select distinct day_start
        from (
            select {{ dbt.date_trunc('day', 'ts_start') }} as day_start from intervals
            union all
            select {{ dbt.date_trunc('day', 'ts_end') }} as day_start from intervals
        ) as bounds
    ) as distinct_days

),

interval_days as (

    select
        d.day_start,
        i.market_id,
        i.interest,
        i.revenue,
        i.is_stuck,
        i.interval_seconds,
        {{ dbt.datediff('greatest(i.ts_start, d.day_start)', 'least(i.ts_end, d.day_end)', 'second') }}
                                                                    as seconds_in_day
    from intervals as i
    inner join days as d
        on  d.day_start < i.ts_end
        and d.day_end > i.ts_start

),

fees_daily as (

    select
        day_start                                                   as day,
        market_id,
        sum(seconds_in_day) / 86400                                 as day_coverage,
        sum(case when is_stuck then 0 else interest * seconds_in_day / interval_seconds end)
                                                                    as fees,
        sum(case when is_stuck then 0 else revenue * seconds_in_day / interval_seconds end)
                                                                    as revenue,
        sum(case when is_stuck then interest * seconds_in_day / interval_seconds else 0 end)
                                                                    as stuck_interest
    from interval_days
    group by 1, 2

),

liquidations_daily as (

    select
        {{ dbt.date_trunc('day', 'l.block_ts') }}                  as day,
        l.market_id,
        count(*)                                                    as n_liquidations,
        -- Morpho.sol (liquidate) sets seized * oracle price = repaid * LIF, so
        -- the liquidator's incentive in loan units is repaid * (LIF - 1), with
        -- LIF = min(1.15, 1 / (0.3 * lltv + 0.7)) (constants in ConstantsLib.sol).
        sum(l.repaid_assets * (least(1.15, 1 / (0.3 * m.lltv + 0.7)) - 1))
                                                                    as liquidation_incentive
    from {{ ref('stg_morpho__events_liquidate') }} as l
    inner join {{ ref('stg_morpho__markets') }} as m
        on m.market_id = l.market_id
    where 1 = 1
        {{ roster_filter('l.market_id') }}
    group by 1, 2

)

select
    coalesce(f.day, l.day)                                          as day,
    m.market_id,
    m.market_label,
    m.loan_asset_symbol,
    coalesce(f.day_coverage, 0)                                     as day_coverage,
    coalesce(f.fees, 0)                                             as fees_loan_units,
    coalesce(f.fees, 0) - coalesce(f.revenue, 0)                    as supply_side_fees_loan_units,
    coalesce(f.revenue, 0)                                          as revenue_loan_units,
    coalesce(f.stuck_interest, 0)                                   as stuck_interest_loan_units,
    coalesce(l.n_liquidations, 0)                                   as n_liquidations,
    coalesce(l.liquidation_incentive, 0)                            as liquidation_incentive_loan_units
from fees_daily as f
full outer join liquidations_daily as l
    on  l.day = f.day
    and l.market_id = f.market_id
inner join {{ ref('stg_morpho__markets') }} as m
    on m.market_id = coalesce(f.market_id, l.market_id)
