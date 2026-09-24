"""Build a small, deterministic Parquet cache for CI runs of the dbt project.

The real cache (data/cache/*.parquet) is gitignored and needs RPC, subgraph
and DEX access to rebuild. CI needs something that honours the exact PyArrow
schemas of src/morpho_stress/data/schemas.py, so this script derives a
synthetic cache from the committed backtest fixtures (data/fixtures/*/):
the three hypothetical markets, their snapshot state and their hourly price
series. Flows, positions and liquidations are simulated with a fixed seed, and
the state samples follow the contract's accounting (MarketLedger), so the fees
models can rebuild interest from them exactly as they do on the real cache.

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
import math
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
YEAR_SECONDS = 365 * 24 * 3600
VIRTUAL_SHARES = 1e6  # shares per asset unit at market creation (SharesMathLib)
MAX_UTILIZATION = 0.97
# The committed fixtures all have a zero fee. One market gets a protocol fee
# so CI exercises the revenue path of the fees models.
FEE_OVERRIDE = {"usdc_depeg_2023_03": 0.10}


class MarketLedger:
    """Totals of one Morpho Blue market as Morpho.sol books them.

    Interest is booked only when a transaction touches the market
    (_accrueInterest), at a constant borrow rate here. The protocol fee is
    minted as supply shares on that interest, and bad debt is taken from both
    totals. States are read as eth_call returns them: stored totals, without
    the interest accrued since the last transaction.
    """

    def __init__(self, supply: float, borrow: float, rate: float, fee: float, start: datetime):
        self.supply, self.borrow = supply, borrow
        self.supply_shares = supply * VIRTUAL_SHARES
        self.borrow_shares = borrow * VIRTUAL_SHARES
        self.rate, self.fee, self.last_update = rate, fee, start

    def accrue(self, ts: datetime) -> None:
        elapsed = (ts - self.last_update).total_seconds()
        if elapsed <= 0:
            return
        interest = self.borrow * math.expm1(self.rate * elapsed / YEAR_SECONDS)
        self.borrow += interest
        self.supply += interest
        fee_amount = interest * self.fee
        # Same pricing as Morpho.sol: the supply already includes the fee amount.
        self.supply_shares += fee_amount * self.supply_shares / (self.supply - fee_amount)
        self.last_update = ts

    def flow(self, kind: str, assets: float) -> tuple[float, float]:
        """Apply one flow, capped to keep utilization at or below MAX_UTILIZATION.

        Returns the (assets, shares) actually moved; zero assets means no event.
        """
        if kind == "withdraw":
            assets = min(assets, self.supply - self.borrow / MAX_UTILIZATION)
        elif kind == "borrow":
            assets = min(assets, self.supply * MAX_UTILIZATION - self.borrow)
        elif kind == "repay":
            assets = min(assets, self.borrow)
        if assets <= 0:
            return 0.0, 0.0
        if kind in ("supply", "withdraw"):
            shares = assets * self.supply_shares / self.supply
            sign = 1 if kind == "supply" else -1
            self.supply += sign * assets
            self.supply_shares += sign * shares
        else:
            shares = assets * self.borrow_shares / self.borrow
            sign = 1 if kind == "borrow" else -1
            self.borrow += sign * assets
            self.borrow_shares += sign * shares
        return assets, shares

    def liquidate(self, repaid: float, bad_debt: float) -> tuple[float, float]:
        """Repay part of a position, then write off bad debt on both sides."""
        repaid_shares = repaid * self.borrow_shares / self.borrow
        self.borrow -= repaid
        self.borrow_shares -= repaid_shares
        bad_debt_shares = bad_debt * self.borrow_shares / self.borrow
        self.borrow -= bad_debt
        self.borrow_shares -= bad_debt_shares
        self.supply -= bad_debt
        return repaid_shares, bad_debt_shares


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

        # Flows and liquidations are drawn first, then played in block order on
        # the ledger. Each state sample is the ledger after its block, so an
        # event in the sample's block is already in that sample, as on chain.
        market_id = m["market_id"].lower()
        price0 = float(m["oracle_price_at_snapshot"])
        lltv = float(m["lltv"])
        fee = FEE_OVERRIDE.get(fixture_dir.name, float(m.get("fee", 0.0)))
        ledger = MarketLedger(
            float(m["total_supply_assets"]),
            float(m["total_borrow_assets"]),
            float(m["rate_at_target_at_snapshot"]),
            fee,
            t0,
        )

        actors = [fake_address(rng) for _ in range(12)]
        planned = []
        for _ in range(FLOW_EVENTS_PER_MARKET):
            offset = float(rng.uniform(0, STATE_DAYS * 24 * 3600))
            planned.append(
                {
                    "block": block_at(t0 + timedelta(seconds=offset)),
                    "log_index": int(rng.integers(0, 300)),
                    "tx_hash": fake_hash(rng),
                    "kind": ["supply", "withdraw", "borrow", "repay"][int(rng.integers(4))],
                    "actor": actors[int(rng.integers(len(actors)))],
                    # Gross flows sized as a fraction of the supply at the time.
                    "fraction": float(rng.lognormal(-6, 1)),
                }
            )
        # Liquidations: two on the market that failed in the backtest fixture
        # (a non-zero bad debt on one of them), none elsewhere.
        if m["collateral_asset_symbol"] == "rsETH":
            for j, bad_debt in enumerate([0.0, 12_500.0]):
                planned.append(
                    {
                        "block": block_at(snapshot_ts - timedelta(hours=6 * (j + 1))),
                        "log_index": 7 + j,
                        "tx_hash": fake_hash(rng),
                        "kind": "liquidate",
                        "actor": actors[0],
                        "borrower": actors[1 + j],
                        "bad_debt": bad_debt,
                    }
                )
        planned.sort(key=lambda e: (e["block"], e["log_index"], e["tx_hash"]))

        # Liquidation incentive factor (ConstantsLib.sol): seized * price = repaid * LIF.
        lif = min(1.15, 1 / (0.3 * lltv + 0.7))
        n_samples = STATE_DAYS * 24 // STATE_STEP_HOURS + 1
        k = 0
        for i in range(n_samples):
            sample_ts = t0 + timedelta(hours=STATE_STEP_HOURS * i)
            sample_block = block_at(sample_ts)
            while k < len(planned) and planned[k]["block"] <= sample_block:
                e = planned[k]
                k += 1
                ts = t0 + timedelta(seconds=(e["block"] - block0) * BLOCK_SECONDS)
                ledger.accrue(ts)
                base = {
                    "market_id": market_id,
                    "block_number": e["block"],
                    "block_ts": ts,
                    "tx_hash": e["tx_hash"],
                    "log_index": e["log_index"],
                }
                if e["kind"] == "liquidate":
                    repaid = ledger.supply * 0.002
                    repaid_shares, bad_debt_shares = ledger.liquidate(repaid, e["bad_debt"])
                    liquidates.append(
                        {
                            **base,
                            "liquidator": e["actor"],
                            "borrower": e["borrower"],
                            "repaid_assets": repaid,
                            "repaid_shares": repaid_shares,
                            "seized_assets": repaid * lif / price0,
                            "bad_debt_assets": e["bad_debt"],
                            "bad_debt_shares": bad_debt_shares,
                        }
                    )
                    continue
                assets, shares = ledger.flow(e["kind"], ledger.supply * e["fraction"])
                if assets <= 0:
                    continue
                row = {
                    **base,
                    "caller": e["actor"],
                    "on_behalf": e["actor"],
                    "assets": assets,
                    "shares": shares,
                }
                if e["kind"] == "supply":
                    supplies.append(row)
                elif e["kind"] == "withdraw":
                    withdraws.append({**row, "receiver": e["actor"]})
                elif e["kind"] == "borrow":
                    borrows.append({**row, "receiver": e["actor"]})
                else:
                    repays.append(row)
            states.append(
                {
                    "market_id": market_id,
                    "block_number": sample_block,
                    "block_ts": sample_ts,
                    "total_supply_assets": ledger.supply,
                    "total_supply_shares": ledger.supply_shares,
                    "total_borrow_assets": ledger.borrow,
                    "total_borrow_shares": ledger.borrow_shares,
                    "total_collateral": ledger.borrow * 1.4 / price0,
                    # Market.lastUpdate is the timestamp of the last accrual.
                    "last_update": int(ledger.last_update.timestamp()),
                    "fee": fee,
                }
            )
        assert k == len(planned), "an event falls after the last state sample"
        borrow = ledger.borrow

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
