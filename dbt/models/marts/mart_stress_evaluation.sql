{#- Publication table enriched with market parameters and the pinned cached
    state. Every stress figure (alpha_star, tiers, Monte Carlo probabilities,
    extreme-scenario flags) is passed through from the Python engine
    unchanged: tests/assert_alpha_star_passthrough.sql fails the build if a
    join or a rewrite ever alters it. supply_assets stays in the market's
    own loan asset; no cross-asset total exists in this project. -#}
select
    e.market_id,
    e.market_label,
    e.state_block,
    e.supply_assets,
    e.utilization,
    e.n_positions,
    e.alpha,
    e.alpha_star,
    e.lsr24,
    e.tti_hours,
    e.p_bad_debt,
    e.p_insolvency,
    e.insolvency_p99_pct,
    e.bad_debt_p99_pct,
    e.drawdown_source,
    e.drawdown_observations,
    e.tier,
    e.severity,
    e.tti_severity,
    e.solvency_severity,
    e.attention_severity,
    e.extreme_drawdown_used,
    e.lsr24_extreme,
    e.bad_debt_extreme_realized_pct,
    e.insolvency_extreme_pct,
    e.extreme_illiq_fail,
    e.extreme_insolv_fail,
    e.extreme_fail,
    e.notes,
    -- Market parameters and cached state (null when the cache is not populated).
    g.loan_asset_symbol,
    g.collateral_asset_symbol,
    g.lltv,
    g.oracle_type,
    g.roster_rank,
    p.cached_state_block,
    p.total_supply_assets                       as cached_total_supply_assets,
    p.total_borrow_assets                       as cached_total_borrow_assets,
    p.utilization                               as cached_utilization
from {{ ref('stg_publication__evaluation_results') }} as e
left join {{ ref('mart_market_registry') }} as g
    on g.market_id = e.market_id
left join {{ ref('int_morpho__market_state_pinned') }} as p
    on p.market_id = e.market_id
