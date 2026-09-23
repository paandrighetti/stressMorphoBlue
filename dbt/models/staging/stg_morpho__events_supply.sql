select
    {{ event_base_columns('e') }},
    'supply'                                                     as event_type,
    lower(e.caller)                                             as caller,
    lower(e.on_behalf)                                          as on_behalf,
    cast(null as {{ dbt.type_string() }})                                                 as receiver,
    e.assets                                                    as assets,
    e.shares                                                    as shares
from {{ source('morpho_cache', 'events_supply') }} as e
