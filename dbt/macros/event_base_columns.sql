{#- Base columns shared by every Morpho Blue event table in the cache.
    event_key is the natural primary key of a decoded log: a transaction hash
    is unique per chain and log_index orders logs inside it. -#}
{% macro event_base_columns(alias='e') %}
    {{ alias }}.tx_hash || '-' || cast({{ alias }}.log_index as {{ dbt.type_string() }}) as event_key,
    lower({{ alias }}.market_id) as market_id,
    cast({{ alias }}.block_number as {{ dbt.type_bigint() }}) as block_number,
    {{ alias }}.block_ts as block_ts,
    {{ alias }}.tx_hash as tx_hash,
    cast({{ alias }}.log_index as {{ dbt.type_bigint() }}) as log_index
{% endmacro %}

{#- Roster filter used by the event-derived models. Off in CI, where the
    fixture cache contains hypothetical markets that are not on the roster. -#}
{% macro roster_filter(column='market_id') %}
    {% if var('monitored_only') %}
    and {{ column }} in (select market_id from {{ ref('roster_markets') }})
    {% endif %}
{% endmacro %}
