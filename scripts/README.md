# Data acquisition pipeline

These scripts populate `data/cache/*.parquet` from on-chain and off-chain
sources. They form the Phase 2 deliverable described in
[`docs/DATA.md`](../docs/DATA.md).

## Pre-requisites

1. Python environment with the project installed: `pip install -e ".[dev]"`
2. A `config.local.yaml` at the project root with:
   - `network.rpc_url` (Alchemy or other Ethereum mainnet endpoint)
   - `subgraph.url` and `subgraph.api_key` (for events and market discovery)
   - `morpho_blue.contract` (default mainnet address, do not change unless
     pointing to a fork)
   - `range.start_ts` and `range.end_ts` (UTC timestamps)
   - `sampling.*` cadences (default values are sensible)
   - `markets:` (list of market ids; fill by running
     `scripts/select_markets.py` first)

3. Free-tier API accounts:
   - Alchemy (or any other Ethereum RPC provider)
   - The Graph (for the Morpho Blue subgraph)
   - DeFiLlama (no auth required)

## Pipeline order (dependencies)

```
   select_markets.py         (subgraph)
            ↓
       fetch_markets.py      (RPC; needs config.markets populated)
            ↓
   ┌────────┼────────┬──────────────────────────┐
   ↓        ↓        ↓                          ↓
 fetch_  fetch_   fetch_                      fetch_
 market_ events.  oracle_                     uniswap_
 state.  py       prices.py                   quotes.py
 py      (sub-    (RPC)                       (RPC)
 (RPC)   graph)
                                  ↓
                          fetch_tvl.py
                          (DeFiLlama, independent)
```

## Step-by-step usage

```bash
# Activate venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\Activate.ps1        # Windows (PowerShell)

# 1. Discover top-N markets and patch config.local.yaml
python scripts/select_markets.py --top 10 --in-place   # WARNING: REPLACES the curated roster in config; do not run to refresh an existing study

# 2. Fetch market metadata (RPC). ~1-5 min for 10 markets.
python scripts/fetch_markets.py

# 3. Fetch TVL (DeFiLlama). ~10 sec, no dependencies.
python scripts/fetch_tvl.py

# 4. Fetch market state time series (RPC). 5-30 min depending on cadence
#    and number of markets.
python scripts/fetch_market_state.py

# 5. Fetch oracle prices (RPC). 2-10 min.
python scripts/fetch_oracle_prices.py

# 6. Fetch events from subgraph. 1-5 min.
python scripts/fetch_events.py

# 7. Quote slippage curve via Uniswap V3 Quoter (RPC). 1-2 min.
python scripts/fetch_uniswap_quotes.py
```

## Idempotence

Each script is idempotent: re-running with the same configuration
produces the same output (modulo the most recent block, which advances
between runs). Output files are versioned in `data/manifest.json` with
SHA-256 checksums for reproducibility.

## Provider limits and retries

RPC, indexing and market-data quotas vary by provider, plan and date. Consult
the current provider documentation and account dashboards before a fresh run;
do not rely on hard-coded free-tier figures in this repository. Start with a
small market sample when validating new credentials or endpoints.

The data clients use retry and exponential-backoff policies. If a provider
returns sustained rate-limit errors, reduce concurrency or adjust the retry
configuration in `src/morpho_stress/data/{rpc,subgraph}.py` rather than assuming
that a missing response represents missing market data.

## Validation after fetch

```bash
# Inspect what was written
python -c "
import duckdb
con = duckdb.connect('data/catalog.duckdb', read_only=True)
print(con.execute('DESCRIBE markets').df())
print(con.execute('SELECT loan_asset_symbol, collateral_asset_symbol, lltv FROM markets').df())
"

# Run all tests, including the data-layer tests
PYTHONPATH=src pytest tests/data/ -v
```

If any Parquet write fails the schema check, the script exits non-zero
and writes nothing. Type drift will not silently corrupt the cache.

## v1.1 evaluation chain (after the fetch steps above)

```
python scripts/fetch_positions_api.py     # live position book via the Morpho API
python scripts/fetch_agg_quotes.py        # keyless exotic-collateral depth (CoW, KyberSwap)
python scripts/pendle_csv_to_slippage.py  # merge Pendle-router curves for PT collateral
python scripts/run_evaluation.py          # 26-market evaluation -> docs/evaluation_results.csv
python scripts/generate_report_tables.py  # -> docs/_generated/*.md
python scripts/assemble_docs.py           # splices the figures into README, REPORT, MIRROR
```
