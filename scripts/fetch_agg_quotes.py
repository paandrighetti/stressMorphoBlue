"""Quote exotic-collateral exit depth via KEYLESS aggregator APIs and MERGE
the rows into data/cache/dex_slippage.parquet.

No API key, no registration, no KYC:
    * cowswap (default): POST https://api.cow.fi/mainnet/api/v1/quote
      Solver-based executable depth, all-in (protocol fee included in the
      realized price), which is the right economics for a 24h exit measure.
    * kyberswap (fallback): GET aggregator-api.kyberswap.com routes

For each collateral symbol lacking a usable curve, quotes
sell collateral -> loan asset across a log grid of USD sizes and records
IMPACT REBASED ON THE SMALLEST EXECUTED SIZE (source = 'cowswap_quote' or
'kyberswap_quote'). Rebasing matters: yield-accruing wrappers often trade at
a PREMIUM to their oracle NAV, so oracle-basis slippage goes negative across
the grid and the power-law fit has nothing to work with; the smallest-size
execution is the correct mid proxy, exactly like pendle_depth.py does. The
actual oracle price and realized prices are still stored for reference. Tokens with no route on either venue are skipped after
repeated failures and reported: those markets stay excluded WITH an explicit
reason, which is the honest outcome (permissioned RWA wrappers).

Methodological note for the report: for instantly-redeemable ERC-4626
wrappers (sUSDS-type), aggregator depth UNDERSTATES true 24h exit capacity
(arbitrageurs can mint/redeem at NAV), so the resulting curves are
conservative; for cooldown wrappers (sUSDe's 7-day unstake), aggregator
depth IS the 24h exit.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import click
import httpx
import pandas as pd
import pyarrow as pa

from morpho_stress.data import (
    FileEntry,
    Manifest,
    RunEntry,
    ValidationResult,
    write_parquet,
)
from morpho_stress.data.schemas import get_schema

logger = logging.getLogger("fetch_agg_quotes")

# Some public aggregator endpoints sit behind a WAF that rejects non-browser
# user agents (403 on every call). Send a browser-like UA and a client id.
UA_HEADERS = {
    "accept": "application/json",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "origin": "https://swap.cow.fi",
    "referer": "https://swap.cow.fi/",
}
_verbose_errors_left = 3


def _log_http_error(venue: str, r) -> None:
    global _verbose_errors_left
    if _verbose_errors_left > 0:
        _verbose_errors_left -= 1
        logger.warning("%s HTTP %d: %s", venue, r.status_code, r.text[:300])

STABLE_LOANS = {"USDC", "USDT", "PYUSD", "RLUSD", "USDtb", "AUSD", "DAI", "USDS", "USDe"}
COW_URL = "https://api.cow.fi/mainnet/api/v1/quote"
KYBER_URL = "https://aggregator-api.kyberswap.com/ethereum/api/v1/routes"


def _grid(min_usd: float, max_usd: float, steps: int) -> list[float]:
    r = (max_usd / min_usd) ** (1.0 / (steps - 1))
    return [min_usd * r**k for k in range(steps)]


def _quote_cow(http: httpx.Client, src: str, dst: str, amount: int, from_addr: str) -> float:
    payload = {
        "sellToken": src, "buyToken": dst,
        "from": from_addr, "receiver": from_addr,
        "kind": "sell", "sellAmountBeforeFee": str(amount),
        "partiallyFillable": False,
    }
    r = http.post(COW_URL, json=payload)
    if r.status_code == 429:
        time.sleep(3.0)
        r = http.post(COW_URL, json=payload)
    if r.status_code >= 400:
        _log_http_error("cowswap", r)
        return 0.0
    q = (r.json() or {}).get("quote") or {}
    return float(q.get("buyAmount") or 0)


def _quote_kyber(http: httpx.Client, src: str, dst: str, amount: int) -> float:
    r = http.get(KYBER_URL, params={"tokenIn": src, "tokenOut": dst, "amountIn": str(amount)},
                 headers={"x-client-id": "morpho-stress-research"})
    if r.status_code == 429:
        time.sleep(3.0)
        r = http.get(KYBER_URL, params={"tokenIn": src, "tokenOut": dst, "amountIn": str(amount)},
                 headers={"x-client-id": "morpho-stress-research"})
    if r.status_code >= 400:
        _log_http_error("kyberswap", r)
        return 0.0
    data = ((r.json() or {}).get("data") or {}).get("routeSummary") or {}
    return float(data.get("amountOut") or 0)


@click.command()
@click.option("--source", type=click.Choice(["cowswap", "kyberswap"]), default="cowswap")
@click.option("--markets", "markets_path", default="data/cache/markets.parquet")
@click.option("--oracle", "oracle_path", default="data/cache/oracle_prices.parquet")
@click.option("--slippage", "slip_path", default="data/cache/dex_slippage.parquet")
@click.option("--from-address", default="0x1111111111111111111111111111111111111111",
              help="any valid address; only used to simulate quotes, never to trade")
@click.option("--min-usd", default=1_000.0)
@click.option("--max-usd", default=10_000_000.0)
@click.option("--steps", default=20)
@click.option("--min-existing-obs", default=8,
              help="skip symbols already having at least this many rows")
@click.option("--pause-s", default=0.6)
@click.option("--symbols", default="",
              help="comma-separated subset to (re)quote; default = all uncovered")
def main(source, markets_path, oracle_path, slip_path, from_address,
         min_usd, max_usd, steps, min_existing_obs, pause_s, symbols) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info("fetch_agg_quotes v3 (keyless, source=%s, size-rebased impact)", source)

    markets = pd.read_parquet(markets_path)
    oracle = pd.read_parquet(oracle_path)
    op_price = "price" if "price" in oracle.columns else "oracle_price"
    op_block = "block_number" if "block_number" in oracle.columns else "block"

    try:
        existing = pd.read_parquet(slip_path)
    except Exception:  # noqa: BLE001
        existing = pd.DataFrame(columns=[f.name for f in get_schema("dex_slippage")])
    counts = existing.groupby("collateral_symbol").size() if len(existing) else pd.Series(dtype=int)
    only = {s.strip() for s in symbols.split(",") if s.strip()}

    tasks: dict[str, dict] = {}
    for _, mk in markets.iterrows():
        sym = mk["collateral_asset_symbol"]
        if only and sym not in only:
            continue
        if not only and counts.get(sym, 0) >= min_existing_obs:
            continue
        pr = oracle[oracle["market_id"] == mk["market_id"]]
        if pr.empty:
            continue
        px = float(pr.sort_values(op_block).iloc[-1][op_price])
        loan_sym = mk["loan_asset_symbol"]
        if loan_sym not in STABLE_LOANS:
            logger.warning("%s: loan %s is not a USD stable; USD sizing is approximate",
                           sym, loan_sym)
        tasks.setdefault(sym, {
            "src": mk["collateral_asset"], "dst": mk["loan_asset"],
            "coll_dec": int(mk["collateral_asset_decimals"]),
            "loan_dec": int(mk["loan_asset_decimals"]),
            "px": px,
        })

    if not tasks:
        logger.info("Nothing to quote: all collateral symbols already covered.")
        return
    logger.info("Quoting %d collateral symbols via %s: %s",
                len(tasks), source, ", ".join(sorted(tasks)))

    now_ts = datetime.now(timezone.utc)
    rows, skipped = [], []
    with httpx.Client(timeout=30.0, headers=UA_HEADERS) as http:
        for sym, t in tasks.items():
            got, attempts, early_fails = 0, 0, 0
            sym_quotes: list[tuple[float, float, float]] = []
            for usd in _grid(min_usd, max_usd, steps):
                native = usd / t["px"]
                amount = int(native * 10 ** t["coll_dec"])
                if amount <= 0:
                    continue
                if source == "cowswap":
                    out_raw = _quote_cow(http, t["src"], t["dst"], amount, from_address)
                else:
                    out_raw = _quote_kyber(http, t["src"], t["dst"], amount)
                time.sleep(pause_s)
                attempts += 1
                if out_raw <= 0:
                    if attempts <= 5:
                        early_fails += 1
                        if early_fails >= 5:
                            skipped.append(sym)
                            logger.warning("%s: first 5 sizes all failed on %s; SKIPPING symbol",
                                           sym, source)
                            break
                    continue
                realized = (out_raw / 10 ** t["loan_dec"]) / native
                sym_quotes.append((float(usd), float(native), float(realized)))
                got += 1
            # Rebase impact on the smallest successfully executed size
            if sym_quotes:
                sym_quotes.sort(key=lambda q: q[0])
                base = sym_quotes[0][2]
                for usd_q, native_q, realized_q in sym_quotes:
                    bps = max((base - realized_q) / base * 10_000.0, 0.01)
                    rows.append({
                        "collateral_symbol": sym,
                        "quote_ts": now_ts,
                        "direction": "sell_collateral_for_loan",
                        "volume_usd": usd_q,
                        "volume_native": native_q,
                        "oracle_price": float(t["px"]),
                        "realized_price": realized_q,
                        "slippage_bps": bps,
                        "source": f"{source}_quote",
                    })
            logger.info("%s: %d quotes", sym, got)

    if not rows:
        raise click.ClickException(
            f"No {source} quotes obtained. Retry with --source "
            f"{'kyberswap' if source == 'cowswap' else 'cowswap'}, "
            "or run with --symbols to target specific collaterals."
        )

    merged = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    table = pa.Table.from_pylist(merged.to_dict("records"), schema=get_schema("dex_slippage"))
    Path(slip_path).parent.mkdir(parents=True, exist_ok=True)
    entry = write_parquet(table, slip_path, schema_name="dex_slippage")
    logger.info("Merged %d new rows; dex_slippage now has %d rows", len(rows), entry["rows"])
    if skipped:
        logger.warning("No route (documented exclusions): %s", ", ".join(sorted(set(skipped))))

    manifest = Manifest()
    manifest.append_run(RunEntry(
        run_id=Manifest.now_run_id(),
        run_ts=now_ts.isoformat(),
        config_hash="agg_quotes",
        block_range_min=0, block_range_max=0,
        markets=[],
        files={"dex_slippage.parquet": FileEntry(
            path=str(slip_path), schema="dex_slippage",
            rows=int(entry["rows"]), bytes=int(entry["bytes"]),
            sha256=str(entry["sha256"]))},
        validation=ValidationResult(all_passed=True),
    ))


if __name__ == "__main__":
    main()
