{#- Weekly gross flows per loan asset and flow type (dune/dune_queries.sql, Q4).
    Grouped by loan asset and never summed across assets: USDC and WETH
    amounts are not commensurable without an exchange-rate assumption, and
    the framework makes none. -#}
select
    {{ dbt.date_trunc('week', 'block_ts') }}    as week_start,
    loan_asset_symbol,
    flow_type,
    ledger,
    count(*)                                    as n_events,
    sum(amount_loan_units)                      as gross_amount_loan_units,
    sum(signed_amount_loan_units)               as signed_amount_loan_units
from {{ ref('int_morpho__flow_events') }}
group by 1, 2, 3, 4
