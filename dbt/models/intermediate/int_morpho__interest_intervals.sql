{#- Interest booked by Morpho Blue between two consecutive state samples of a
    market, from the contract's accounting (Morpho.sol, _accrueInterest and
    liquidate). Over the blocks (block_start, block_end]:
      borrow ledger:  B1 = B0 + borrowed - repaid - liquidation repaid - bad debt + interest
      supply ledger:  S1 = S0 + supplied - withdrawn - bad debt + interest
      supply shares: SS1 = SS0 + supply shares - withdraw shares + fee shares
    Each asset ledger gives the interest on its own, from the state reads and
    the events of the interval; tests/assert_interest_ledgers_agree.sql checks
    that they match. The share ledger measures the fee shares actually minted
    to the fee recipient, which tests/assert_fee_shares_match_fee.sql compares
    with interest times the fee parameter.
    Balances still come from the state reads: flows only explain the change
    between two reads, they are never cumulated into a balance.
    The contract books interest when a transaction touches the market, so an
    interval without activity shows zero interest and the next one catches up.
    The interest booked between two reads accrued exactly between their
    Market.lastUpdate values (accrued_from_unix, accrued_to_unix). -#}
{#- A table rather than a view: the fees mart, the tests and the snapshot
    export all read it, and the range join is the costly step. -#}
{{ config(materialized='table') }}

with states as (

    select
        market_id,
        lag(block_number) over w                    as block_start,
        block_number                                as block_end,
        lag(block_ts) over w                        as ts_start,
        block_ts                                    as ts_end,
        lag(total_supply_assets) over w             as supply_assets_start,
        total_supply_assets                         as supply_assets_end,
        lag(total_supply_shares) over w             as supply_shares_start,
        total_supply_shares                         as supply_shares_end,
        lag(total_borrow_assets) over w             as borrow_assets_start,
        total_borrow_assets                         as borrow_assets_end,
        lag(utilization) over w                     as utilization_start,
        utilization                                 as utilization_end,
        lag(fee) over w                             as fee_start,
        fee                                         as fee_end,
        lag(last_update_unix) over w                as accrued_from_unix,
        last_update_unix                            as accrued_to_unix
    from {{ ref('stg_morpho__market_state') }}
    where 1 = 1
        {{ roster_filter('market_id') }}
    window w as (partition by market_id order by block_number)

),

events as (

    select market_id, block_number, flow_type, amount_loan_units as assets, shares,
           cast(0 as {{ dbt.type_float() }}) as bad_debt_assets
    from {{ ref('int_morpho__flow_events') }}

    union all

    select market_id, block_number, 'liquidate', repaid_assets, repaid_shares, bad_debt_assets
    from {{ ref('stg_morpho__events_liquidate') }}
    where 1 = 1
        {{ roster_filter('market_id') }}

),

-- The event cache covers one fetch window for every market. An interval is
-- covered when it lies between the first and the last cached event, which
-- is conservative: it can only drop intervals, never keep a partial one.
event_window as (

    select
        min(block_number)                           as first_event_block,
        max(block_number)                           as last_event_block
    from events

),

interval_flows as (

    select
        s.market_id,
        s.block_end,
        count(*)                                                                    as n_events,
        sum(case when e.flow_type = 'supply'    then e.assets else 0 end)           as supplied,
        sum(case when e.flow_type = 'withdraw'  then e.assets else 0 end)           as withdrawn,
        sum(case when e.flow_type = 'borrow'    then e.assets else 0 end)           as borrowed,
        sum(case when e.flow_type = 'repay'     then e.assets else 0 end)           as repaid,
        sum(case when e.flow_type = 'liquidate' then e.assets else 0 end)           as liquidation_repaid,
        sum(e.bad_debt_assets)                                                      as bad_debt,
        sum(case when e.flow_type = 'supply'    then e.shares else 0 end)
            - sum(case when e.flow_type = 'withdraw' then e.shares else 0 end)      as net_supply_shares
    from states as s
    inner join events as e
        on  e.market_id = s.market_id
        and e.block_number > s.block_start
        and e.block_number <= s.block_end
    group by 1, 2

),

intervals as (

    select
        s.*,
        coalesce(f.n_events, 0)                     as n_events,
        coalesce(f.bad_debt, 0)                     as bad_debt,
        (s.borrow_assets_end - s.borrow_assets_start)
            - (coalesce(f.borrowed, 0) - coalesce(f.repaid, 0)
               - coalesce(f.liquidation_repaid, 0) - coalesce(f.bad_debt, 0))
                                                    as interest_borrow_ledger,
        (s.supply_assets_end - s.supply_assets_start)
            - (coalesce(f.supplied, 0) - coalesce(f.withdrawn, 0) - coalesce(f.bad_debt, 0))
                                                    as interest_supply_ledger,
        (s.supply_shares_end - s.supply_shares_start) - coalesce(f.net_supply_shares, 0)
                                                    as fee_shares_minted,
        s.block_start >= w.first_event_block
            and s.block_end <= w.last_event_block   as is_covered
    from states as s
    cross join event_window as w
    left join interval_flows as f
        on  f.market_id = s.market_id
        and f.block_end = s.block_end
    where s.block_start is not null

)

select
    market_id,
    block_start,
    block_end,
    ts_start,
    ts_end,
    supply_assets_start,
    supply_assets_end,
    borrow_assets_start,
    borrow_assets_end,
    utilization_start,
    utilization_end,
    fee_start,
    fee_end,
    accrued_from_unix,
    accrued_to_unix,
    n_events,
    bad_debt,
    -- Fees in Token Terminal's sense: interest paid by borrowers, taken from
    -- the borrow ledger (smaller totals, so less floating-point noise). The
    -- supply ledger is kept as the independent check.
    interest_borrow_ledger                          as interest,
    interest_supply_ledger,
    -- The contract mints fee shares worth interest * fee; with the fee
    -- unchanged inside the interval this is exact.
    interest_borrow_ledger * fee_start              as revenue,
    fee_shares_minted,
    fee_shares_minted * supply_assets_end / nullif(supply_shares_end, 0)
                                                    as fee_shares_value_end,
    is_covered,
    -- Pinned at full utilization at both reads. The interest booked there
    -- raises suppliers' claims while no cash is left to withdraw at the reads;
    -- the mart reports it apart from fees (docs/FEES.md, section 3).
    coalesce(utilization_start >= {{ var('stuck_utilization') }}
             and utilization_end >= {{ var('stuck_utilization') }}, false)
                                                    as is_stuck
from intervals
