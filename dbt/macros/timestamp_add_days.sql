{#- Add whole days to a timestamp and keep the timestamp type. dbt.dateadd
    returns a DATETIME on BigQuery, which cannot be compared with a TIMESTAMP. -#}
{% macro timestamp_add_days(ts, n) %}
    {{ return(adapter.dispatch('timestamp_add_days')(ts, n)) }}
{% endmacro %}

{% macro default__timestamp_add_days(ts, n) %}
    {{ dbt.dateadd('day', n, ts) }}
{% endmacro %}

{% macro bigquery__timestamp_add_days(ts, n) %}
    timestamp_add({{ ts }}, interval {{ n }} day)
{% endmacro %}
