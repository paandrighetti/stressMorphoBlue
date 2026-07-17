"""scripts/enrich_positions.py.

Reconstruct active borrower positions from Borrow / Repay event streams.

This replaces the parametric Beta-scaled position distribution used by
default in `forward_looking._profile_to_state` with empirically derived
position-level loan-to-values. Each active borrower's net borrow balance
is reconstructed by aggregating their Borrow events minus their Repay
events over the analysis window.

Limitations:
    - We reconstruct net BORROW balances, not collateral balances.
      The collateral balance per borrower is approximated by allocating
      the market's total_collateral pro-rata to net-borrow share. This
      is a simplification: the true collateral allocation requires
      processing SupplyCollateral and WithdrawCollateral events, which
      are not currently in the cache. A future iteration should add them.
    - Borrowers who have fully repaid their position have a net balance
      of zero and are excluded.
    - The pro-rata collateral allocation assumes uniform LTV across
      borrowers within a market. The actual cross-borrower variance
      cannot be measured without collateral events.

Output:
    data/cache/positions.parquet (per-borrower per-market net balance,
    reconstructed LTV, allocated collateral)

The downstream `enrich_forward_looking.py` reads this file (when
present) and uses the reconstructed LTVs in lieu of the Beta-scaled
distribution.

Usage:
    python scripts/enrich_positions.py --config config.local.yaml
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from morpho_stress.config import Config

logger = logging.getLogger(__name__)


POSITIONS_SCHEMA = pa.schema([
    ("market_id", pa.string()),
    ("borrower", pa.string()),
    ("net_borrow_assets", pa.float64()),
    ("allocated_collateral_native", pa.float64()),
    ("ltv", pa.float64()),
    ("market_label", pa.string()),
])


def _aggregate_net_borrow(
    borrow_events: pd.DataFrame, repay_events: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate net borrow balances per (market_id, borrower).

    Net balance = sum(borrow.assets) - sum(repay.assets) over the analysis
    window. Negative values are clipped to zero (borrowers who repaid
    more than they borrowed in the window: typically pre-window borrows
    repaid in-window).
    """
    if borrow_events.empty:
        return pd.DataFrame(columns=["market_id", "borrower", "net_borrow_assets"])

    borrow_agg = (
        borrow_events.groupby(["market_id", "on_behalf"])["assets"]
        .sum()
        .reset_index()
        .rename(columns={"on_behalf": "borrower", "assets": "borrowed"})
    )
    if repay_events.empty:
        repay_agg = pd.DataFrame(columns=["market_id", "borrower", "repaid"])
    else:
        repay_agg = (
            repay_events.groupby(["market_id", "on_behalf"])["assets"]
            .sum()
            .reset_index()
            .rename(columns={"on_behalf": "borrower", "assets": "repaid"})
        )

    merged = borrow_agg.merge(repay_agg, on=["market_id", "borrower"], how="left")
    merged["repaid"] = merged["repaid"].fillna(0.0)
    merged["net_borrow_assets"] = (merged["borrowed"] - merged["repaid"]).clip(lower=0.0)

    # Drop rows with zero net balance (positions fully repaid)
    return merged[merged["net_borrow_assets"] > 1e-6][
        ["market_id", "borrower", "net_borrow_assets"]
    ].copy()


def reconstruct_positions(
    markets: pd.DataFrame,
    market_state: pd.DataFrame,
    events_borrow: pd.DataFrame,
    events_repay: pd.DataFrame,
    oracle_prices: pd.DataFrame,
) -> pd.DataFrame:
    """Reconstruct active positions for every market in `markets`.

    For each (market_id, borrower) with positive net borrow balance:
        1. Compute share = net_borrow / sum(net_borrows for that market)
        2. allocated_collateral = share * total_collateral_native
        3. ltv = (net_borrow_loan_unit) / (allocated_collateral_native * oracle_price_per_collateral_unit)

    The oracle_price used is the most recent observation per market.
    Net borrows are scaled down by sum-of-net to handle the case where
    aggregated borrows from events exceed total_borrow (events span a
    longer window than the latest state).
    """
    # Latest market state per market
    if "block_number" in market_state.columns:
        latest_state = (
            market_state.sort_values("block_number").drop_duplicates("market_id", keep="last")
        )
    else:
        latest_state = market_state.drop_duplicates("market_id", keep="last")
    state_by_market = latest_state.set_index("market_id")

    # Latest oracle price per market
    if not oracle_prices.empty and "block_number" in oracle_prices.columns:
        latest_oracle = (
            oracle_prices.sort_values("block_number")
            .drop_duplicates("market_id", keep="last")
            .set_index("market_id")
        )
    else:
        latest_oracle = oracle_prices.drop_duplicates("market_id", keep="last").set_index("market_id") if not oracle_prices.empty else pd.DataFrame()

    # Aggregate net borrows per (market, borrower)
    net_borrows = _aggregate_net_borrow(events_borrow, events_repay)

    if net_borrows.empty:
        logger.warning("No active borrowers reconstructed from events")
        return pd.DataFrame(columns=POSITIONS_SCHEMA.names)

    rows: list[dict] = []
    market_meta_by_id = markets.set_index("market_id")

    for market_id, group in net_borrows.groupby("market_id"):
        if market_id not in market_meta_by_id.index:
            continue
        if market_id not in state_by_market.index:
            continue

        meta = market_meta_by_id.loc[market_id]
        state = state_by_market.loc[market_id]
        label = f"{meta['collateral_asset_symbol']}/{meta['loan_asset_symbol']}"

        # Total collateral in native units (collateral asset)
        total_coll_native = float(state.get("total_collateral", 0.0))
        if total_coll_native <= 0:
            logger.debug("Market %s has zero total_collateral; skipping", label)
            continue

        # Latest oracle price (loan units per 1 collateral unit, normalised)
        if market_id not in latest_oracle.index:
            logger.warning("Market %s has no oracle price; skipping", label)
            continue
        oracle_price = float(latest_oracle.loc[market_id, "price"])
        if oracle_price <= 0:
            continue

        # Share of net borrow per borrower
        sum_net = float(group["net_borrow_assets"].sum())
        if sum_net <= 0:
            continue

        # Cap net borrows at the actual current total_borrow_assets to
        # avoid over-counting events that span more than the current state
        actual_total_borrow = float(state.get("total_borrow_assets", 0.0))
        scale_factor = min(1.0, actual_total_borrow / sum_net) if sum_net > 0 else 0.0

        for _, row in group.iterrows():
            net_borrow = float(row["net_borrow_assets"]) * scale_factor
            if net_borrow <= 0:
                continue
            share = net_borrow / max(actual_total_borrow, 1e-9)
            allocated_coll = share * total_coll_native
            if allocated_coll <= 0:
                continue
            # LTV = borrow_value / collateral_value (both in loan units)
            collateral_value_loan_units = allocated_coll * oracle_price
            ltv = net_borrow / collateral_value_loan_units if collateral_value_loan_units > 0 else 0.0
            ltv = float(min(ltv, 1.0))  # cap at 1 (above means under-collateralised)
            rows.append({
                "market_id": market_id,
                "borrower": str(row["borrower"]),
                "net_borrow_assets": net_borrow,
                "allocated_collateral_native": allocated_coll,
                "ltv": ltv,
                "market_label": label,
            })

    return pd.DataFrame(rows)


@click.command()
@click.option(
    "--config",
    "config_path",
    default="config.local.yaml",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--cache-dir",
    default="data/cache",
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--output",
    "output_path",
    default="data/cache/positions_reconstructed.parquet",
    type=click.Path(dir_okay=False),
)
def main(config_path: str, cache_dir: str, output_path: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.load(config_path)

    cache_root = Path(cache_dir)

    markets = pq.read_table(cache_root / "markets.parquet").to_pandas()
    market_state = pq.read_table(cache_root / "market_state.parquet").to_pandas()
    events_borrow = pq.read_table(cache_root / "events_borrow.parquet").to_pandas()

    repay_path = cache_root / "events_repay.parquet"
    if repay_path.exists():
        events_repay = pq.read_table(repay_path).to_pandas()
    else:
        events_repay = pd.DataFrame()

    oracle_path = cache_root / "oracle_prices.parquet"
    if oracle_path.exists():
        oracle_prices = pq.read_table(oracle_path).to_pandas()
    else:
        oracle_prices = pd.DataFrame()

    logger.info(
        "Loaded: markets=%d, market_state=%d, events_borrow=%d, events_repay=%d, oracle_prices=%d",
        len(markets), len(market_state), len(events_borrow), len(events_repay), len(oracle_prices),
    )

    positions = reconstruct_positions(
        markets, market_state, events_borrow, events_repay, oracle_prices
    )

    if positions.empty:
        raise click.ClickException("No positions reconstructed; check input data")

    logger.info(
        "Reconstructed %d positions across %d markets",
        len(positions), positions["market_id"].nunique(),
    )
    logger.info(
        "LTV summary: mean=%.3f, median=%.3f, p95=%.3f, p99=%.3f",
        positions["ltv"].mean(),
        positions["ltv"].median(),
        positions["ltv"].quantile(0.95),
        positions["ltv"].quantile(0.99),
    )

    table = pa.Table.from_pandas(positions, schema=POSITIONS_SCHEMA, preserve_index=False)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_path, compression="zstd")
    n_bytes = Path(output_path).stat().st_size
    logger.info("Wrote %d positions to %s (%d bytes)", len(positions), output_path, n_bytes)


if __name__ == "__main__":
    main()
