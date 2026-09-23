-- Every monitored market is either evaluated or excluded with a reason.
select market_id, roster_rank, coverage_status
from {{ ref('mart_roster_coverage') }}
where coverage_status = 'missing'
