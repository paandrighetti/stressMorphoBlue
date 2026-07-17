"""Fetch CURRENT per-borrower positions from the Morpho API (marketPositions).

Bypasses the event-replay path (`enrich_positions.py`) for the live snapshot:
the API serves the positions directly, so no dependence on event-history
completeness or on the skip-pagination cap. Writes `positions.parquet` with
the exact schema of docs/DATA.md §3.4, stamped at the latest sampled
market_state block per market (fetch market_state right before this script so
the two snapshots are near-simultaneous; the per-market coverage ratio
sum(borrow_shares) / market_state.total_borrow_shares is logged as the
sanity check of DATA.md §5.3).

Usage:
    python scripts/fetch_positions_api.py --config config.local.yaml

If the Morpho API schema drifts again (GraphQL 400), the script introspects
the MarketPosition type, prints the available fields, and exits with a clear
message: paste that output to adapt the query.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import click
import pandas as pd
import pyarrow as pa

from morpho_stress.config import Config
from morpho_stress.data import (
    FileEntry,
    Manifest,
    RunEntry,
    ValidationResult,
    write_parquet,
)
from morpho_stress.data.schemas import get_schema
from morpho_stress.data.subgraph import SubgraphClient

logger = logging.getLogger("fetch_positions_api")

INTROSPECT_QUERY = """
query Introspect($name: String!) {
  __type(name: $name) {
    name
    kind
    fields { name type { name kind ofType { name kind } } }
    inputFields { name }
  }
}
"""

QUERY_ARGS_QUERY = """
{
  __type(name: "Query") {
    fields {
      name
      args { name type { name kind ofType { name kind } } }
    }
  }
}
"""


def _type_info(client: SubgraphClient, name: str) -> dict:
    result = client._post(INTROSPECT_QUERY, {"name": name})
    return result.get("__type") or {}


def _field_names(t: dict) -> list[str]:
    out = [f["name"] for f in (t.get("fields") or [])]
    out += [f["name"] for f in (t.get("inputFields") or [])]
    return out


def _unwrap_type_name(tref: dict) -> str | None:
    while tref and not tref.get("name"):
        tref = tref.get("ofType") or {}
    return tref.get("name") if tref else None


def build_adaptive_query(client: SubgraphClient) -> tuple[str, bool, str]:
    """Introspect the live schema and assemble the positions query.

    Returns (query_string, needs_chain_id, description).
    """
    # a) where-input type of Query.marketPositions
    qt = client._post(QUERY_ARGS_QUERY, {}).get("__type") or {}
    mp = next((f for f in qt.get("fields") or [] if f["name"] == "marketPositions"), None)
    if mp is None:
        raise click.ClickException("The API no longer exposes Query.marketPositions")
    where_arg = next((a for a in mp.get("args") or [] if a["name"] == "where"), None)
    filters = _field_names(_type_info(client, _unwrap_type_name(where_arg["type"]))) if where_arg else []

    mkt_filter = next((f for f in ("marketUniqueKey_in", "marketUniqueKeys_in", "uniqueKey_in")
                       if f in filters), None)
    if mkt_filter is None:
        mkt_filter = next((f for f in filters if "arket" in f and f.endswith("_in")), None)
    if mkt_filter is None:
        raise click.ClickException(f"No market filter found on marketPositions; filters: {filters}")
    chain_filter = "chainId_in" if "chainId_in" in filters else None

    # b) selection set on MarketPosition (state nested or flat)
    pos_t = _type_info(client, "MarketPosition")
    pos_fields = {f["name"]: f for f in (pos_t.get("fields") or [])}
    wanted = ("borrowShares", "borrowAssets", "collateral", "supplyShares")
    if "state" in pos_fields:
        state_type = _unwrap_type_name(pos_fields["state"]["type"])
        state_fields = _field_names(_type_info(client, state_type or ""))
        picks = [w for w in wanted if w in state_fields]
        if not picks:
            raise click.ClickException(f"No usable fields on {state_type}: {state_fields}")
        selection = "user { address } state { " + " ".join(picks) + " }"
        nested = True
    else:
        picks = [w for w in wanted if w in pos_fields]
        if not picks:
            raise click.ClickException(f"No usable fields on MarketPosition: {list(pos_fields)}")
        selection = "user { address } " + " ".join(picks)
        nested = False

    where_parts = [f"{mkt_filter}: [$marketUniqueKey]"]
    var_defs = ["$first: Int!", "$skip: Int!", "$marketUniqueKey: String!"]
    if chain_filter:
        where_parts.append(f"{chain_filter}: [$chainId]")
        var_defs.append("$chainId: Int!")

    query = (
        "query MarketPositions(" + ", ".join(var_defs) + ") {\n"
        "  marketPositions(first: $first, skip: $skip, where: { "
        + ", ".join(where_parts) + " }) {\n"
        "    items { " + selection + " }\n"
        "  }\n"
        "}"
    )
    desc = (f"filter={mkt_filter}" + (f"+{chain_filter}" if chain_filter else "")
            + f", selection={'state{' + ' '.join(picks) + '}' if nested else ' '.join(picks)}")
    return query, chain_filter is not None, desc


def _introspect(client: SubgraphClient, type_name: str) -> str:
    try:
        # _post returns body["data"] already unwrapped (see SubgraphClient)
        result = client._post(INTROSPECT_QUERY, {"name": type_name})
        t = result.get("__type") or {}
        fields = ", ".join(f["name"] for f in (t.get("fields") or []))
        return f"{type_name}: {fields or '<type not found>'}"
    except Exception as exc:  # noqa: BLE001 - diagnostic path
        return f"{type_name}: introspection failed ({exc})"


@click.command()
@click.option("--config", "config_path", default="config.local.yaml")
@click.option("--markets", "markets_path", default="data/cache/markets.parquet")
@click.option("--state", "state_path", default="data/cache/market_state.parquet")
@click.option("--oracle", "oracle_path", default="data/cache/oracle_prices.parquet")
@click.option("--output", "output_path", default="data/cache/positions.parquet")
@click.option("--page-size", default=100)
@click.option("--chain-id", default=1, help="Ethereum mainnet = 1")
def main(config_path: str, markets_path: str, state_path: str,
         oracle_path: str, output_path: str, page_size: int, chain_id: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("fetch_positions_api v3 (adaptive schema)")

    cfg = Config.load(config_path)
    if not cfg.subgraph or not cfg.subgraph.url:
        raise click.ClickException("config.subgraph.url is required (Morpho API endpoint)")

    markets = pd.read_parquet(markets_path)
    mstate = pd.read_parquet(state_path)
    try:
        oracle = pd.read_parquet(oracle_path)
    except Exception:  # noqa: BLE001
        oracle = None

    block_col = "block_number" if "block_number" in mstate.columns else "block"
    latest = mstate.sort_values(block_col).groupby("market_id").tail(1).set_index("market_id")

    rows: list[dict] = []
    dumped_raw = False
    with SubgraphClient(cfg.subgraph.url, cfg.subgraph.api_key) as client:
        positions_query, needs_chain, desc = build_adaptive_query(client)
        logger.info("Adaptive query built: %s", desc)
        for _, mk in markets.iterrows():
            mid = mk["market_id"]
            label = f"{mk.get('collateral_asset_symbol','?')}/{mk.get('loan_asset_symbol','?')}"
            loan_dec = int(mk.get("loan_asset_decimals", mk.get("loan_decimals", 18)))
            coll_dec = int(mk.get("collateral_asset_decimals", mk.get("collateral_decimals", 18)))
            lltv = float(mk["lltv"]) if float(mk["lltv"]) <= 1 else float(mk["lltv"]) / 1e18

            if mid in latest.index:
                snap = latest.loc[mid]
                blk = int(snap[block_col])
                blk_ts = pd.Timestamp(snap["block_ts"]) if "block_ts" in snap.index else pd.Timestamp.now(tz="UTC")
                total_bs = float(snap.get("total_borrow_shares", float("nan")))
            else:
                blk, blk_ts, total_bs = 0, pd.Timestamp.now(tz="UTC"), float("nan")

            price = float("nan")
            if oracle is not None:
                op = oracle[oracle["market_id"] == mid]
                if not op.empty:
                    pcol = "price" if "price" in op.columns else "oracle_price"
                    price = float(op.sort_values(block_col if block_col in op.columns else op.columns[0]).iloc[-1][pcol])

            skip = 0
            fetched = 0
            sum_bs = 0.0
            while True:
                try:
                    variables = {"first": page_size, "skip": skip, "marketUniqueKey": mid}
                    if needs_chain:
                        variables["chainId"] = chain_id
                    result = client._post(positions_query, variables)
                except Exception as exc:  # GraphQL 400 → introspect and abort with details
                    diag = "\n  ".join(
                        _introspect(client, t)
                        for t in ("MarketPosition", "MarketPositionState",
                                  "MarketPositionFilters", "PublicUser")
                    )
                    raise click.ClickException(
                        f"marketPositions query failed on {label}: {exc}\n"
                        f"Available fields per the live schema:\n  {diag}\n"
                        f"Paste this output back to adapt POSITIONS_QUERY."
                    ) from exc

                # _post returns body["data"] already unwrapped: no second unwrap
                items = ((result.get("marketPositions") or {}).get("items")) or []
                if not items and skip == 0 and total_bs == total_bs and total_bs > 0 and not dumped_raw:
                    logger.warning("RAW response for %s (debt>0 but 0 items): %s",
                                   label, str(result)[:800])
                    dumped_raw = True
                for it in items:
                    st = it.get("state") or it  # nested or flat schema
                    bs = float(st.get("borrowShares") or 0) / 10**loan_dec
                    ba = float(st.get("borrowAssets") or 0) / 10**loan_dec
                    coll = float(st.get("collateral") or 0) / 10**coll_dec
                    if bs <= 0 and coll <= 0:
                        continue
                    ltv = (ba / (coll * price)) if (coll > 0 and price == price and price > 0) else float("nan")
                    rows.append({
                        "market_id": mid,
                        "borrower": ((it.get("user") or {}).get("address") or "0x0").lower(),
                        "block_number": blk,
                        "block_ts": blk_ts.to_pydatetime() if hasattr(blk_ts, "to_pydatetime") else blk_ts,
                        "borrow_shares": bs,
                        "collateral": coll,
                        "borrow_assets": ba,
                        "ltv": ltv,
                        "health_factor": (lltv / ltv) if ltv == ltv and ltv > 0 else float("nan"),
                    })
                    sum_bs += bs
                fetched += len(items)
                if len(items) < page_size:
                    break
                skip += page_size

            cover = (sum_bs / total_bs) if total_bs and total_bs == total_bs and total_bs > 0 else float("nan")
            note = "" if cover != cover or 0.95 <= cover <= 1.05 else "  <-- CHECK (window/state drift?)"
            logger.info("%-28s positions=%4d  borrow-shares coverage=%.3f%s",
                        label, fetched, cover if cover == cover else -1.0, note)

    if not rows:
        raise click.ClickException("No positions fetched; check API output above")

    table = pa.Table.from_pylist(rows, schema=get_schema("positions"))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    entry = write_parquet(table, output_path, schema_name="positions")
    logger.info("Wrote %d position rows to %s", entry["rows"], output_path)

    manifest = Manifest()
    manifest.append_run(RunEntry(
        run_id=Manifest.now_run_id(),
        run_ts=datetime.now(timezone.utc).isoformat(),
        config_hash=Manifest.hash_config(cfg.model_dump(mode="json")),
        block_range_min=int(min(r["block_number"] for r in rows)),
        block_range_max=int(max(r["block_number"] for r in rows)),
        markets=sorted({r["market_id"] for r in rows}),
        files={"positions.parquet": FileEntry(
            path=str(output_path), schema="positions",
            rows=int(entry["rows"]), bytes=int(entry["bytes"]),
            sha256=str(entry["sha256"]),
        )},
        validation=ValidationResult(all_passed=True),
    ))


if __name__ == "__main__":
    main()
