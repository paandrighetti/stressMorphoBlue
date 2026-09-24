{#- Borrower activity concentration per market (dune/dune_queries.sql, Q3).
    Shares are ratios within one market, so units cancel. This is an
    activity proxy: it counts addresses that borrowed inside the window,
    not current balances. Panel titles must say "activity", never
    "current borrowers".
    Numerators and denominator are summed over the same rows in one
    aggregation, so a share is exactly 1 when every borrower is in the top N.
    A window total summed in another order gave 1.0000000000000002 on the
    real cache and failed the [0, 1] bounds test. -#}
with borrow_activity as (

    select
        market_id,
        on_behalf                               as borrower,
        sum(assets)                             as borrowed_loan_units
    from {{ ref('stg_morpho__events_borrow') }}
    where block_ts >= cast('{{ var("activity_window_start") }}' as {{ dbt.type_timestamp() }})
        {{ roster_filter('market_id') }}
    group by 1, 2

),

ranked as (

    select
        market_id,
        borrower,
        borrowed_loan_units,
        row_number() over (
            partition by market_id
            order by borrowed_loan_units desc, borrower
        )                                       as borrower_rank
    from borrow_activity

)

select
    r.market_id,
    m.market_label,
    m.loan_asset_symbol,
    count(*)                                    as n_active_borrowers,
    sum(r.borrowed_loan_units)                  as activity_total_loan_units,
    sum(case when r.borrower_rank <= 3  then r.borrowed_loan_units else 0 end)
        / sum(r.borrowed_loan_units)            as top3_share,
    sum(case when r.borrower_rank <= 10 then r.borrowed_loan_units else 0 end)
        / sum(r.borrowed_loan_units)            as top10_share
from ranked as r
inner join {{ ref('stg_morpho__markets') }} as m
    on m.market_id = r.market_id
group by 1, 2, 3
having sum(r.borrowed_loan_units) > 0
