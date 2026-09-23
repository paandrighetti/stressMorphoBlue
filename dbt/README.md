# dbt port of the SQL layer

This directory ports the SQL side of the framework to a [dbt](https://docs.getdbt.com/) project:
the Dune dashboard queries (`dune/dune_queries.sql`) become tested, documented models, and the
publication table (`docs/evaluation_results.csv`) is exposed through a layer that can only pass it
through. It runs on DuckDB over the local Parquet cache with no load step, and carries a BigQuery
target for the same models.

## Two rules the models enforce

1. **No stress figure is computed in SQL.** `alpha_star`, tiers, Monte Carlo probabilities and the
   extreme-scenario flags depend on measured exit depth, fitted slippage curves and a 200-path
   simulation. They exist only in the Python engine. `tests/assert_alpha_star_passthrough.sql`
   fails the build if a join duplicates, drops or rewrites a published value;
   `tests/assert_tier_consistent_with_alpha_star.sql` checks the published tiers against the
   published thresholds (red below 10 %, yellow below 30 %, green at or above 30 %).
2. **No balance is rebuilt from flows.** Morpho Blue accrues interest through separate
   `AccrueInterest` events, so `sum(supply) - sum(withdraw)` understates the outstanding position
   and the error grows with utilisation. Balances come from contract state reads
   (`stg_morpho__market_state`, `int_morpho__market_state_pinned`); flow models expose gross flows
   only, grouped by loan asset and never summed across assets.

## Layers

| Layer | Path | Content |
|---|---|---|
| 1. Raw | `models/sources.yml` | The Parquet cache (`data/cache/*.parquet`, one canonical source per table, schemas in `src/morpho_stress/data/schemas.py`) and the frozen publication CSV, read in place. |
| 2. Staging | `models/staging/` | One model per source table: typing, lower-cased identifiers, natural keys (`event_key = tx_hash-log_index`), the `collateral/loan` market label. No joins, no business logic. |
| 3. Intermediate | `models/intermediate/` | Unit discipline and windows: signed flow ledger, weekly flows per loan asset, daily liquidations, borrower activity concentration, state pinned at the publication block. |
| 4. Marts | `models/marts/` | Consumer tables: market registry, enriched publication table, roster coverage, and the three dashboard panels (Dune Q2, Q3, Q4). Materialised as tables. |

Lineage, column descriptions and test coverage are in the generated docs (`dbt docs generate`).

## Tests

* Schema tests on every key: `unique`, `not_null`, `relationships` to the market registry,
  `accepted_values` on categorical columns, a dependency-free `bounds` test on ratios.
* Singular tests for the framework invariants: no over-borrow in state samples, strictly increasing
  sample timestamps, decimal-normalised flow units, no cross-asset row in the flows panel, full roster
  coverage (every monitored market is evaluated or excluded with a documented reason), and the two
  publication guards above.
* One dbt unit test (`flow_sign_convention`) pins the sign convention of the flow ledger on mocked
  inputs, independent of any data.

## Running it

```bash
pip install -r dbt/requirements.txt   # pinned: dbt-core 1.11.15, dbt-duckdb 1.11.0, duckdb 1.5.5
cd dbt

# On the real cache produced by scripts/fetch_*.py (data/cache/*.parquet):
dbt build --profiles-dir .

# On the synthetic fixture cache, as CI does (hypothetical markets, roster filter off):
python scripts/build_fixture_cache.py --out fixtures/cache
MORPHO_CACHE_DIR=$PWD/fixtures/cache dbt build --profiles-dir . \
  --vars '{monitored_only: false, activity_window_start: 2000-01-01, liquidation_window_start: 2000-01-01}'

dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .
```

`--vars` is parsed as YAML, so the quote-free form above works unchanged in PowerShell
(set the cache directory there with `$env:MORPHO_CACHE_DIR = "$PWD/fixtures/cache"`).

Variables (`dbt_project.yml`): `state_block` (publication block from `docs/evaluation_manifest.json`),
`liquidation_window_start` and `activity_window_start` (dashboard windows), `monitored_only`
(restrict event-derived models to the 26 markets of `markets_top.yaml`).

Seeds are generated, not hand-edited: `scripts/sync_seeds.py` rebuilds `roster_markets.csv` from
`markets_top.yaml` and `evaluation_exclusions.csv` from `docs/evaluation_summary.json`; CI fails on drift.

## Fixture cache

`scripts/build_fixture_cache.py` derives a small deterministic cache (seed 42) from the committed
backtest fixtures (`data/fixtures/*/market.json` and `prices.csv`): the three hypothetical markets,
their snapshot state, hourly oracle prices, simulated flows, positions and two liquidations (one with
bad debt, so the liquidation panel and its tests see a non-zero value). It uses the exact PyArrow
schemas of the acquisition layer, so a schema change breaks CI here as well as in the Python tests.
Nothing in it is a finding.

## BigQuery

`profiles.yml` carries a `bigquery` target, not exercised in CI. Install the adapter, load the cache
into the source dataset once, then run with `--target bigquery`:

```bash
pip install dbt-bigquery
for t in markets market_state events_supply events_withdraw events_borrow events_repay events_liquidate positions oracle_prices; do
  bq load --source_format=PARQUET "$GCP_PROJECT:morpho_raw.$t" "../data/cache/$t.parquet"
done
bq load --source_format=CSV --autodetect "$GCP_PROJECT:morpho_raw.evaluation_results" ../docs/evaluation_results.csv
dbt build --profiles-dir . --target bigquery
```

The models use dbt's cross-database macros (`dbt.date_trunc`, `dbt.type_*`) and standard SQL
(window functions, `full outer join`); the `external_location` metadata is ignored outside DuckDB.
