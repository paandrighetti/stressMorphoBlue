{#- Dashboard panel: weekly gross flows per loan asset (Q4). Chart one series
    per loan asset; never draw a single total line across assets. -#}
select *
from {{ ref('int_morpho__flows_weekly') }}
where week_start >= cast('{{ var("activity_window_start") }}' as {{ dbt.type_timestamp() }})
