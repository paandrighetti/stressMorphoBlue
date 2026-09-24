"""scripts/fetch_events.py: fetch Morpho Blue events via the Morpho API.

Uses the `marketTransactions` query at api.morpho.org/graphql with
`marketUniqueKey_in`, `type_in` and `chainId_in` filters. The former
`transactions` query was deprecated on 2026-04-23 and later removed
(Morpho API changelog).

Outputs:
    data/cache/events_supply.parquet
    data/cache/events_withdraw.parquet
    data/cache/events_borrow.parquet
    data/cache/events_repay.parquet
    data/cache/events_liquidate.parquet

Time-range filtering and pagination:
    The config.range window is applied by the API (timestamp_gte and
    timestamp_lte), and pages are chained with the API cursor (txHash and
    logIndex of the last event read), newest first. Each (market, event type)
    must return exactly the pageInfo.countTotal announced by the API, or the
    fetch fails.

    Skip pagination is not used: measured on 2026-09-24, the API returns
    short pages (999 events for first: 1000) that read as the end of the
    data, loses events that share a timestamp across page boundaries, and
    rejects skip values beyond about 10,000. With the window applied
    client-side on top of it, the fetch returned 0 supply and 0 withdraw
    events for cbBTC/USDC on a one-month window holding 7,146 and 10,441.

Schema reference:
    https://docs.morpho.org/tools/offchain/api/morpho/
    https://docs.morpho.org/developers/api/changelog/

Usage:
    python scripts/fetch_events.py --config config.local.yaml [--event-types supply,liquidate]
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import click
import pyarrow as pa
import pyarrow.parquet as pq

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

logger = logging.getLogger(__name__)


# Mapping of internal event types to Morpho API MarketTransactionType enum values
EVENT_TYPE_TO_API = {
    "supply": "Supply",
    "withdraw": "Withdraw",
    "borrow": "Borrow",
    "repay": "Repay",
    "liquidate": "Liquidation",
}


# GraphQL query on `marketTransactions`.
# Filters: marketUniqueKey_in (array), type_in (array of MarketTransactionType
# enum), chainId_in pinned to Ethereum mainnet, the only chain of the roster
# and of the publication (docs/evaluation_manifest.json, chain_id 1), and the
# config.range window (timestamp_gte, timestamp_lte, in seconds). $cursor is
# the (txHash, logIndex) of the last event read; the API documents it as an
# exact anchor. pageInfo.countTotal counts the events after the cursor, so the
# total of the window is the one returned with the first page.
# Schema-drift note (2026-07): the API removed `uniqueKey` from the `Market`
# type reachable through transaction data, which used to 400 the whole fetch.
# We never needed it: the market identity comes from the $marketUniqueKey
# filter variable, so the selection was dropped entirely.
# Schema-drift note (2026-09): `transactions` was removed in favour of
# `marketTransactions`; items expose `txHash` instead of `hash` and the data
# union members were renamed MarketTransaction*Data.
EVENTS_QUERY = """
query MarketEvents(
  $first: Int!
  $marketUniqueKey: String!
  $typeIn: [MarketTransactionType!]
  $timestampGte: Int!
  $timestampLte: Int!
  $cursor: MarketTransactionCursorInput
) {
  marketTransactions(
    first: $first
    orderBy: Timestamp
    orderDirection: Desc
    where: {
      marketUniqueKey_in: [$marketUniqueKey]
      type_in: $typeIn
      chainId_in: [1]
      timestamp_gte: $timestampGte
      timestamp_lte: $timestampLte
      cursor: $cursor
    }
  ) {
    pageInfo { countTotal }
    items {
      txHash
      logIndex
      timestamp
      blockNumber
      type
      user { address }
      data {
        ... on MarketTransactionTransferData {
          assets
          shares
        }
        ... on MarketTransactionLiquidationData {
          repaidAssets
          repaidShares
          seizedAssets
          badDebtAssets
          badDebtShares
          liquidator
        }
      }
    }
  }
}
"""


def _normalize_event_row(
    event_type: str,
    raw: dict,
    loan_decimals: int,
    collateral_decimals: int,
    market_id: str,
) -> dict | None:
    """Convert a raw Morpho API transaction into our Parquet row.

    Returns None if essential fields are missing.
    """
    try:
        block_ts = datetime.fromtimestamp(int(raw["timestamp"]), tz=timezone.utc)
        # (tx_hash, log_index) is the natural key of an event: one transaction
        # can emit several events of the same type (vault reallocations,
        # bundler multicalls), so the log index is essential.
        log_index = int(raw["logIndex"])
    except (KeyError, ValueError, TypeError):
        return None

    base = {
        "market_id": market_id,
        "block_number": int(raw.get("blockNumber") or 0),
        "block_ts": block_ts,
        "tx_hash": raw.get("txHash") or "0x",
        "log_index": log_index,
    }

    data = raw.get("data") or {}
    user = (raw.get("user") or {}).get("address", "0x0000000000000000000000000000000000000000")
    user = user.lower()

    scale_loan = 10**loan_decimals
    scale_coll = 10**collateral_decimals

    if event_type == "supply":
        return {
            **base,
            "caller": user,
            "on_behalf": user,
            "assets": float(data.get("assets") or 0) / scale_loan,
            "shares": float(data.get("shares") or 0) / scale_loan,
        }
    elif event_type == "withdraw":
        return {
            **base,
            "caller": user,
            "on_behalf": user,
            "receiver": user,
            "assets": float(data.get("assets") or 0) / scale_loan,
            "shares": float(data.get("shares") or 0) / scale_loan,
        }
    elif event_type == "borrow":
        return {
            **base,
            "caller": user,
            "on_behalf": user,
            "receiver": user,
            "assets": float(data.get("assets") or 0) / scale_loan,
            "shares": float(data.get("shares") or 0) / scale_loan,
        }
    elif event_type == "repay":
        return {
            **base,
            "caller": user,
            "on_behalf": user,
            "assets": float(data.get("assets") or 0) / scale_loan,
            "shares": float(data.get("shares") or 0) / scale_loan,
        }
    elif event_type == "liquidate":
        liquidator_addr = data.get("liquidator") or user
        return {
            **base,
            "liquidator": liquidator_addr.lower() if liquidator_addr else user,
            "borrower": user,
            "repaid_assets": float(data.get("repaidAssets") or 0) / scale_loan,
            "repaid_shares": float(data.get("repaidShares") or 0) / scale_loan,
            "seized_assets": float(data.get("seizedAssets") or 0) / scale_coll,
            "bad_debt_assets": float(data.get("badDebtAssets") or 0) / scale_loan,
            "bad_debt_shares": float(data.get("badDebtShares") or 0) / scale_loan,
        }
    else:
        raise ValueError(f"Unknown event type: {event_type}")


def _dedupe_events(rows: list[dict]) -> tuple[list[dict], int]:
    """Keep one row per log (tx_hash, log_index); return the rows and the drop count.

    Cursor pagination should never read a log twice; this is a guard.
    Identical repeats are dropped. Two different payloads under one key would
    be a source defect, so that case raises instead of silently picking one.
    """
    kept: dict[tuple[str, int], dict] = {}
    for row in rows:
        key = (row["tx_hash"], row["log_index"])
        if key not in kept:
            kept[key] = row
        elif kept[key] != row:
            raise ValueError(f"conflicting payloads for event {key}")
    return list(kept.values()), len(rows) - len(kept)


def _fetch_event_type_for_market(
    client: SubgraphClient,
    event_type: str,
    market_id: str,
    start_ts: int,
    end_ts: int,
    loan_decimals: int,
    collateral_decimals: int,
) -> list[dict]:
    """Fetch every event of one type for one market inside [start_ts, end_ts].

    The API filters the window and pages are chained with its cursor until an
    empty page. The number of events kept must equal the countTotal of the
    first page, otherwise the fetch fails instead of writing a partial cache.
    """
    variables = {
        "first": 1000,
        "marketUniqueKey": market_id,
        "typeIn": [EVENT_TYPE_TO_API[event_type]],
        "timestampGte": start_ts,
        "timestampLte": end_ts,
        "cursor": None,
    }
    rows: list[dict] = []
    expected = None

    while True:
        page = client._post(EVENTS_QUERY, variables).get("marketTransactions") or {}
        if expected is None:
            expected = int((page.get("pageInfo") or {}).get("countTotal") or 0)
        items = page.get("items") or []
        if not items:
            break
        for raw in items:
            row = _normalize_event_row(
                event_type, raw, loan_decimals, collateral_decimals, market_id
            )
            if row is not None:
                rows.append(row)
        variables["cursor"] = {"txHash": items[-1]["txHash"], "logIndex": items[-1]["logIndex"]}

    if len(rows) != expected:
        raise RuntimeError(
            f"{event_type}/{market_id}: {len(rows)} events kept, API countTotal {expected}"
        )
    return rows


@click.command()
@click.option(
    "--config",
    "config_path",
    default="config.local.yaml",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--markets-input",
    default="data/cache/markets.parquet",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--output-dir",
    default="data/cache",
    type=click.Path(file_okay=False),
)
@click.option(
    "--event-types",
    default="supply,withdraw,borrow,repay,liquidate",
    help="Comma-separated event types to fetch",
)
def main(config_path: str, markets_input: str, output_dir: str, event_types: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.load(config_path)

    if not cfg.subgraph or not cfg.subgraph.url:
        raise click.ClickException("config.subgraph.url is required (Morpho API endpoint)")

    types_to_fetch = [t.strip() for t in event_types.split(",") if t.strip()]
    invalid = [t for t in types_to_fetch if t not in EVENT_TYPE_TO_API]
    if invalid:
        raise click.ClickException(f"Unknown event types: {invalid}")

    markets_df = pq.read_table(markets_input).to_pylist()
    logger.info("Loaded %d markets; fetching event types: %s", len(markets_df), types_to_fetch)

    start_ts = int(cfg.range.start_ts.timestamp())
    end_ts = int(cfg.range.end_ts.timestamp())

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_files = {}

    with SubgraphClient(cfg.subgraph.url, cfg.subgraph.api_key) as client:
        for event_type in types_to_fetch:
            logger.info("=== Fetching %s events ===", event_type)
            all_rows: list[dict] = []

            for m in markets_df:
                rows = _fetch_event_type_for_market(
                    client,
                    event_type,
                    m["market_id"],
                    start_ts,
                    end_ts,
                    m["loan_asset_decimals"],
                    m["collateral_asset_decimals"],
                )
                logger.info(
                    "  %s/%s: %s: %d events",
                    m["collateral_asset_symbol"],
                    m["loan_asset_symbol"],
                    event_type,
                    len(rows),
                )
                all_rows.extend(rows)

            all_rows, n_repeats = _dedupe_events(all_rows)
            if n_repeats:
                logger.info(
                    "  dropped %d repeated %s rows (pagination overlap)", n_repeats, event_type
                )

            schema_name = f"events_{event_type}"
            output_path = output_root / f"{schema_name}.parquet"

            if not all_rows:
                logger.warning("No %s events found in window; skipping write", event_type)
                continue

            table = pa.Table.from_pylist(all_rows, schema=get_schema(schema_name))
            entry_dict = write_parquet(table, str(output_path), schema_name=schema_name)
            logger.info("Wrote %d rows to %s", entry_dict["rows"], output_path)

            manifest_files[output_path.name] = FileEntry(
                path=str(output_path),
                schema=schema_name,
                rows=int(entry_dict["rows"]),
                bytes=int(entry_dict["bytes"]),
                sha256=str(entry_dict["sha256"]),
            )

    manifest = Manifest()
    manifest.append_run(
        RunEntry(
            run_id=Manifest.now_run_id(),
            run_ts=datetime.now(timezone.utc).isoformat(),
            config_hash=Manifest.hash_config(cfg.model_dump(mode="json")),
            block_range_min=0,
            block_range_max=0,
            markets=[m["market_id"] for m in markets_df],
            files=manifest_files,
            validation=ValidationResult(all_passed=True),
        )
    )


if __name__ == "__main__":
    main()
