{#- Dashboard panel: borrower activity concentration per market (Q3). -#}
select *
from {{ ref('int_morpho__borrower_activity') }}
