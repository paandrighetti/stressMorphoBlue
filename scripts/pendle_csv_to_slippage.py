"""Convert a pendle_depth.py CSV (size_usd, impact) into dex_slippage rows.

The three PT-collateral Morpho markets have no meaningful Uniswap or 1inch
route: their exit venue is the Pendle router. Measure the exit curve with the
llamalend_pt_coverage toolkit (discover_market.py + pendle_depth.py, WITH
--enable-aggregator since the relevant question here is executable exit to
the loan asset, unlike the governance post's Pendle-only measurement), then
merge the curve here.

Example:
    python scripts/pendle_csv_to_slippage.py \
        --csv ..\\llamalend_pt_coverage\\pt_apyusd_depth.csv \
        --collateral-symbol PT-apyUSD-18JUN2026 --pt-usd-price 0.90
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import click
import pandas as pd
import pyarrow as pa

from morpho_stress.data import write_parquet
from morpho_stress.data.schemas import get_schema

logger = logging.getLogger("pendle_csv_to_slippage")


@click.command()
@click.option("--csv", "csv_path", required=True)
@click.option("--collateral-symbol", required=True,
              help="exact symbol as in markets.parquet, e.g. PT-apyUSD-18JUN2026")
@click.option("--pt-usd-price", type=float, required=True,
              help="USD mark per PT used for the pull (pendle_depth --spot-price)")
@click.option("--slippage", "slip_path", default="data/cache/dex_slippage.parquet")
def main(csv_path, collateral_symbol, pt_usd_price, slip_path) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    depth = pd.read_csv(csv_path)
    if not {"size_usd", "impact"}.issubset(depth.columns):
        raise click.ClickException(f"CSV must have size_usd,impact; got {list(depth.columns)}")

    now_ts = datetime.now(timezone.utc)
    rows = [{
        "collateral_symbol": collateral_symbol,
        "quote_ts": now_ts,
        "direction": "sell_collateral_for_loan",
        "volume_usd": float(r.size_usd),
        "volume_native": float(r.size_usd) / pt_usd_price,
        "oracle_price": float(pt_usd_price),
        "realized_price": float(pt_usd_price) * (1.0 - float(r.impact)),
        "slippage_bps": max(float(r.impact) * 10_000.0, 0.01),
        "source": "pendle_router",
    } for r in depth.itertuples() if float(r.size_usd) > 0]

    try:
        existing = pd.read_parquet(slip_path)
    except Exception:  # noqa: BLE001
        existing = pd.DataFrame(columns=[f.name for f in get_schema("dex_slippage")])
    merged = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    table = pa.Table.from_pylist(merged.to_dict("records"), schema=get_schema("dex_slippage"))
    Path(slip_path).parent.mkdir(parents=True, exist_ok=True)
    entry = write_parquet(table, slip_path, schema_name="dex_slippage")
    logger.info("Merged %d Pendle rows for %s; dex_slippage now has %d rows",
                len(rows), collateral_symbol, entry["rows"])


if __name__ == "__main__":
    main()
