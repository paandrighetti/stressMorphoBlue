-- Structural guard on the flows panel: every row is keyed by a loan asset.
-- An unlabelled or 'total' row would mean amounts were summed across assets,
-- the defect that v1.1 of the Dune queries exists to remove.
select *
from {{ ref('mart_flows_weekly') }}
where loan_asset_symbol is null
    or lower(loan_asset_symbol) in ('all', 'total')
