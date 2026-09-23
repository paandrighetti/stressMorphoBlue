-- alpha_star is computed by the Python engine only. The mart must contain
-- exactly one row per published market with the identical alpha_star.
-- Any row here means a join duplicated, dropped or rewrote a figure.
with src as (

    select lower(market_id) as market_id, alpha_star
    from {{ source('publication', 'evaluation_results') }}

),

mart as (

    select market_id, alpha_star, count(*) over (partition by market_id) as n_rows
    from {{ ref('mart_stress_evaluation') }}

)

select
    coalesce(src.market_id, mart.market_id) as market_id,
    src.alpha_star                          as published_alpha_star,
    mart.alpha_star                         as mart_alpha_star
from src
full outer join mart
    on mart.market_id = src.market_id
where src.market_id is null
    or mart.market_id is null
    or mart.n_rows <> 1
    or src.alpha_star <> mart.alpha_star
