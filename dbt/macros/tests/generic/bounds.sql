{#- Range test without pulling dbt_utils: fails on values outside [lower, upper]. -#}
{% test bounds(model, column_name, lower, upper) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} < {{ lower }} or {{ column_name }} > {{ upper }}
{% endtest %}
