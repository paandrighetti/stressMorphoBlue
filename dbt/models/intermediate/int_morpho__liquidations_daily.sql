{#- Daily liquidation activity per market (dune/dune_queries.sql, Q2).
    repaid and bad debt are in the market's loan asset, seized in its
    collateral asset. Each row is labelled with both symbols; do not sum
    these columns across markets with different assets. A non-zero
    bad_debt_loan_units is the falsification surface for the published
    claim that keeper rationality suppresses execution before bad debt
    is booked. -#}
select
    l.market_id,
    m.market_label,
    m.loan_asset_symbol,
    m.collateral_asset_symbol,
    {{ dbt.date_trunc('day', 'l.block_ts') }}   as day,
    count(*)                                    as n_liquidations,
    count(distinct l.borrower)                  as n_borrowers,
    sum(l.repaid_assets)                        as repaid_loan_units,
    sum(l.seized_assets)                        as seized_collateral_units,
    sum(l.bad_debt_assets)                      as bad_debt_loan_units
from {{ ref('stg_morpho__events_liquidate') }} as l
inner join {{ ref('stg_morpho__markets') }} as m
    on m.market_id = l.market_id
where 1 = 1
    {{ roster_filter('l.market_id') }}
group by 1, 2, 3, 4, 5
