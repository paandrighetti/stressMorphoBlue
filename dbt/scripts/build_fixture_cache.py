"""Build a small, deterministic Parquet cache for CI runs of the dbt project.

The real cache (data/cache/*.parquet) is gitignored and needs RPC, subgraph
and DEX access to rebuild. CI needs something that honours the exact PyArrow
schemas of src/morpho_stress/data/schemas.py, so this script derives a
synthetic cache from the committed backtest fixtures (data/fixtures/*/):
the three hypothetical markets, their snapshot state and their hourly price
series. Flows, positions and liquidations are simulated with a fixed seed.

Nothing produced here is a finding. The publication table stays
docs/evaluation_results.csv, which the dbt project reads in place.

Usage:
    python dbt/scripts/build_fixture_cache.py --out data/cache
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "data" / "fixtures"
SEED = 42
BLOCK_SECONDS = 12
STATE_STEP_HOURS = 6
STATE_DAYS = 10
FLOW_EVENTS_PER_MARKET = 120
POSITIONS_PER_MARKET = 20


def load_registry() -> dict[str, pa.Schema]:
    """Import the canonical schemas, with or without the package installed."""
    try:
        from morpho_stress.data.schemas import REGISTRY  # type: ignore

        return REGISTRY
    except ImportError:
        path = REPO / "src" / "morpho_stress" / "data" / "schemas.py"
        spec = importlib.util.spec_from_file_location("morpho_schemas", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module.REGISTRY


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def to_table(rows: list[dict], schema: pa.Schema) -> pa.Table:
    columns = {field.name: [row[field.name] for row in rows] for field in schema}
    return pa.Table.from_pydict(columns, schema=schema)


def fake_address(rng: np.random.Generator) -> str:
    return "0x" + "".join(rng.choice(list("0123456789abcdef"), size=40))


def fake_hash(rng: np.random.Generator) -> str:
    return "0x" + "".join(rng.choice(list("0123456789abcdef"), size=64))


def build(out_dir: Path) -> None:
    registry = load_registry()
    rng = np.random.default_rng(SEED)
    out_dir.mkdir(parents=True, exist_ok=True)

    markets, states, supplies, withdraws, borrows, repays, liquidates = [], [], [], [], [], [], []
    positions, prices = [], []

    for fixture_dir in sorted(FIXTURES.iterdir()):
        market_file = fixture_dir / "market.json"
        if not market_file.exists():
            continue
        m = json.loads(market_file.read_text(encoding="utf-8"))
        snapshot_ts = parse_ts(m["snapshot_ts"])
        snapshot_block = int(m["snapshot_block"])
        t0 = snapshot_ts - timedelta(days=STATE_DAYS)
        block0 = snapshot_block - STATE_DAYS * 24 * 3600 // BLOCK_SECONDS

        def block_at(ts: datetime) -> int:
            return block0 + int((ts - t0).total_seconds()) // BLOCK_SECONDS

        markets.append(
            {
                "market_id": m["market_id"].lower(),
                "loan_asset": fake_address(rng),
                "loan_asset_symbol": m["loan_asset_symbol"],
                "loan_asset_decimals": int(m["loan_asset_decimals"]),
                "collateral_asset": fake_address(rng),
                "collateral_asset_symbol": m["collateral_asset_symbol"],
                "collateral_asset_decimals": int(m["collateral_asset_decimals"]),
                "oracle": fake_address(rng),
                "oracle_type": m.get("oracle_kind", "chainlink"),
                "irm": fake_address(rng),
                "lltv": float(m["lltv"]),
                "created_at_block": block0 - 1_000_000,
                "created_at_ts": t0 - timedelta(days=365),
            }
        )

        # Market state: supply and borrow drift, interest accrual grows both
        # sides slightly between samples. Borrow never exceeds supply.
        supply = float(m["total_supply_assets"])
        borrow = float(m["total_borrow_assets"])
        price0 = float(m["oracle_price_at_snapshot"])
        n_samples = STATE_DAYS * 24 // STATE_STEP_HOURS + 1
        for i in range(n_samples):
            ts = t0 + timedelta(hours=STATE_STEP_HOURS * i)
            accrual = 1 + 0.04 * STATE_STEP_HOURS / (365 * 24)
            supply *= accrual * (1 + rng.normal(0, 0.002))
            borrow = min(borrow * accrual * (1 + rng.normal(0, 0.003)), supply * 0.97)
            states.append(
                {
                    "market_id": m["market_id"].lower(),
                    "block_number": block_at(ts),
                    "block_ts": ts,
                    "total_supply_assets": supply,
                    "total_supply_shares": supply * 1e6,
                    "total_borrow_assets": borrow,
                    "total_borrow_shares": borrow * 1e6,
                    "total_collateral": borrow * 1.4 / price0,
                    "last_update": block_at(ts),
                    "fee": float(m.get("fee", 0.0)),
                }
            )

        # Flow events: gross flows sized as a fraction of supply.
        actors = [fake_address(rng) for _ in range(12)]
        for i in range(FLOW_EVENTS_PER_MARKET):
            ts = t0 + timedelta(seconds=float(rng.uniform(0, STATE_DAYS * 24 * 3600)))
            block = block_at(ts)
            actor = actors[int(rng.integers(len(actors)))]
            amount = float(supply * rng.lognormal(-6, 1))
            base = {
                "market_id": m["market_id"].lower(),
                "block_number": block,
                "block_ts": ts,
                "tx_hash": fake_hash(rng),
                "log_index": int(rng.integers(0, 300)),
                "caller": actor,
                "on_behalf": actor,
                "assets": amount,
                "shares": amount * 1e6,
            }
            kind = ["supply", "withdraw", "borrow", "repay"][int(rng.integers(4))]
            if kind == "supply":
                supplies.append(base)
            elif kind == "withdraw":
                withdraws.append({**base, "receiver": actor})
            elif kind == "borrow":
                borrows.append({**base, "receiver": actor})
            else:
                repays.append(base)

        # Liquidations: two on the market that failed in the backtest fixture
        # (a non-zero bad debt on one of them), none elsewhere.
        if m["collateral_asset_symbol"] == "rsETH":
            for j, bad_debt in enumerate([0.0, 12_500.0]):
                ts = snapshot_ts - timedelta(hours=6 * (j + 1))
                repaid = float(supply * 0.002)
                liquidates.append(
                    {
                        "market_id": m["market_id"].lower(),
                        "block_number": block_at(ts),
                        "block_ts": ts,
                        "tx_hash": fake_hash(rng),
                        "log_index": 7 + j,
                        "liquidator": actors[0],
                        "borrower": actors[1 + j],
                        "repaid_assets": repaid,
                        "repaid_shares": repaid * 1e6,
                        "seized_assets": repaid / price0 * 1.05,
                        "bad_debt_assets": bad_debt,
                        "bad_debt_shares": bad_debt * 1e6,
                    }
                )

        # Positions at the snapshot block.
        for k in range(POSITIONS_PER_MARKET):
            borrow_assets = float(borrow * rng.dirichlet(np.ones(POSITIONS_PER_MARKET))[k])
            ltv = float(min(rng.beta(8, 2) * m["lltv"], m["lltv"] - 1e-4))
            positions.append(
                {
                    "market_id": m["market_id"].lower(),
                    "borrower": fake_address(rng),
                    "block_number": snapshot_block,
                    "block_ts": snapshot_ts,
                    "borrow_shares": borrow_assets * 1e6,
                    "collateral": borrow_assets / (ltv * price0),
                    "borrow_assets": borrow_assets,
                    "ltv": ltv,
                    "health_factor": float(m["lltv"] / ltv),
                }
            )

        # Oracle prices from the committed hourly series, expressed as
        # collateral per loan asset (USD prices divided by the loan price).
        loan_usd = price0 if m["loan_asset_symbol"] == "WETH" else 1.0
        with (fixture_dir / "prices.csv").open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                ts = parse_ts(row["ts"])
                prices.append(
                    {
                        "market_id": m["market_id"].lower(),
                        "block_number": block_at(ts),
                        "block_ts": ts,
                        "price": float(row["oracle_price_usd"]) / loan_usd,
                        "price_decimals_raw": 8,
                        "oracle_kind": m.get("oracle_kind", "chainlink"),
                        "staleness_blocks": int(rng.integers(0, 300)),
                    }
                )

    tables = {
        "markets": markets,
        "market_state": states,
        "events_supply": supplies,
        "events_withdraw": withdraws,
        "events_borrow": borrows,
        "events_repay": repays,
        "events_liquidate": liquidates,
        "positions": positions,
        "oracle_prices": prices,
    }
    for name, rows in tables.items():
        table = to_table(rows, registry[name])
        pq.write_table(table, out_dir / f"{name}.parquet")
        print(f"{name}.parquet: {table.num_rows} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "dbt" / "fixtures" / "cache")
    args = parser.parse_args()
    build(args.out)
