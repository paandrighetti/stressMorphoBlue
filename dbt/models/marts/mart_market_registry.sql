{#- Reference table of Morpho Blue markets in the cache, flagged with roster
    membership (markets_top.yaml) and publication exclusions
    (docs/evaluation_summary.json). Port of dune/dune_queries.sql, Q1. -#}
select
    m.market_id,
    m.market_label,
    m.loan_asset_symbol,
    m.loan_asset_address,
    m.loan_asset_decimals,
    m.collateral_asset_symbol,
    m.collateral_asset_address,
    m.collateral_asset_decimals,
    m.lltv,
    m.oracle_type,
    m.oracle_address,
    m.irm_address,
    m.created_at_block,
    m.created_at_ts,
    r.market_id is not null                     as is_monitored,
    r.roster_rank,
    x.reason                                    as exclusion_reason
from {{ ref('stg_morpho__markets') }} as m
left join {{ ref('roster_markets') }} as r
    on r.market_id = m.market_id
left join {{ ref('evaluation_exclusions') }} as x
    on x.market_id = m.market_id
