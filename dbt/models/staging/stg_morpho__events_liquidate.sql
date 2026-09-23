select
    {{ event_base_columns('e') }},
    'liquidate'                                                 as event_type,
    lower(e.liquidator)                                         as liquidator,
    lower(e.borrower)                                           as borrower,
    e.repaid_assets                                             as repaid_assets,
    e.repaid_shares                                             as repaid_shares,
    e.seized_assets                                             as seized_assets,
    e.bad_debt_assets                                           as bad_debt_assets,
    e.bad_debt_shares                                           as bad_debt_shares
from {{ source('morpho_cache', 'events_liquidate') }} as e
