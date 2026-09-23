{#- Accounting of the 26 monitored markets: each is either evaluated in the
    publication table or excluded with a documented reason. A 'missing'
    status is a publication-consistency defect and fails the build. -#}
select
    r.market_id,
    r.roster_rank,
    coalesce(e.market_label, x.market, g.market_label)  as market_label,
    case
        when e.market_id is not null then 'evaluated'
        when x.market_id is not null then 'excluded'
        else 'missing'
    end                                                 as coverage_status,
    x.reason                                            as exclusion_reason,
    e.tier,
    e.alpha_star,
    e.extreme_fail
from {{ ref('roster_markets') }} as r
left join {{ ref('stg_publication__evaluation_results') }} as e
    on e.market_id = r.market_id
left join {{ ref('evaluation_exclusions') }} as x
    on x.market_id = r.market_id
left join {{ ref('stg_morpho__markets') }} as g
    on g.market_id = r.market_id
