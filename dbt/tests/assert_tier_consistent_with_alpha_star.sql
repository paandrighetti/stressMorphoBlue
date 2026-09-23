-- Publication consistency: the survival-frontier tier is red below 10 %,
-- yellow below 30 %, green at or above 30 % of supply absorbable in 24 h
-- (README, "survival-frontier tier"). SQL does not assign tiers; it checks
-- that the published ones honour the published thresholds.
select market_id, market_label, alpha_star, tier
from {{ ref('mart_stress_evaluation') }}
where not (
       (alpha_star <  0.10 and tier = 'red')
    or (alpha_star >= 0.10 and alpha_star < 0.30 and tier = 'yellow')
    or (alpha_star >= 0.30 and tier = 'green')
)
