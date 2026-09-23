select
    {{ event_base_columns('e') }},
    'withdraw'                                                     as event_type,
    lower(e.caller)                                             as caller,
    lower(e.on_behalf)                                          as on_behalf,
    lower(e.receiver)                                                 as receiver,
    e.assets                                                    as assets,
    e.shares                                                    as shares
from {{ source('morpho_cache', 'events_withdraw') }} as e
