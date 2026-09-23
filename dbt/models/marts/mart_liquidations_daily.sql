{#- Dashboard panel: liquidations on the roster, decimal-normalised (Q2). -#}
select *
from {{ ref('int_morpho__liquidations_daily') }}
where day >= cast('{{ var("liquidation_window_start") }}' as {{ dbt.type_timestamp() }})
