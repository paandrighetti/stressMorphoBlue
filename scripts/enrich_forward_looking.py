"""scripts/enrich_forward_looking.py.

Bridge real on-chain data (data/cache/*.parquet) into the forward-looking
risk evaluator (src/morpho_stress/backtest/forward_looking.py).

Reads:
    data/cache/markets.parquet         (metadata: LLTV, oracle, decimals)
    data/cache/market_state.parquet    (S, B, U time series)
    data/cache/oracle_prices.parquet   (price time series)
    data/cache/dex_slippage.parquet    (DEX quote samples for slippage curve fit)
    data/cache/events_borrow.parquet   (per-borrower aggregation)
    data/cache/events_repay.parquet    (per-borrower aggregation)

Produces:
    A list[MarketProfile] suitable for `evaluate_market` in forward_looking.py.

Optional output:
    data/cache/market_profiles.json    (serialised profiles, for inspection)

Methodology:
    Each MarketProfile is constructed from the latest available on-chain state
    plus parameters fitted from the time series. Specifically:

    - total_supply_usd : last total_supply_assets * latest oracle_price
        (when loan asset is USD-pegged, supply_assets are already in USD;
        for non-USD loan assets we apply a separate USD conversion).
    - utilization     : last total_borrow_assets / total_supply_assets.
    - n_positions     : count of unique borrowers (from events_borrow minus
        events_repay net out, approximated as count_distinct(borrower) on borrow).
    - avg_ltv         : volume-weighted average LTV across all active positions.
        Approximation: we don't reconstruct full position state from events
        (would require collateral events too); we use a heuristic based on
        utilisation U and LLTV: avg_ltv ~= U * lltv * 0.85 (with a 15% margin
        from LLTV for typical curated vault risk policies).
    - oracle_price    : latest price observation.
    - rate_at_target  : market-specific value, default 4% (Morpho mainstream).
        Production extension: read from IRM contract via RPC.
    - slippage_a, _b  : fitted from dex_slippage.parquet via fit_curve().
        Falls back to defaults if insufficient observations.
    - drawdown_p50,
      drawdown_p99   : empirical quantiles of negative log-returns of the
        oracle price series, on a 24h horizon.

Limitations:
    - n_positions is approximated by count of unique borrowers in the borrow
      events; it overestimates actual current count if some borrowers have
      since fully repaid.
    - avg_ltv is approximated; a full reconstruction would require events_supply
      collateral subset (not currently fetched as a distinct stream).
    - rate_at_target is hardcoded; for precision, read the IRM contract.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

import click
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from morpho_stress.backtest.forward_looking import MarketProfile
from morpho_stress.models.slippage import SlippageCurve, fit_curve

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Defaults for fields not derivable from cache
# ---------------------------------------------------------------------------

# Adaptive Curve Interest Rate Model: rate_at_target is the per-market
# steady-state rate. Read from the IRM contract for precision.
# Default 4% covers the most common Morpho mainstream configuration.
DEFAULT_RATE_AT_TARGET = 0.04

# Slippage fallback by asset class. Used when dex_slippage.parquet has
# fewer than 10 observations for a given collateral (the case for assets
# not traded on Uniswap V3, e.g. yield-bearing stablecoin synthetics traded
# primarily on Curve, or principal tokens traded on Pendle).
#
# Calibration rationale:
#   - Stablecoin synthetics: tight peg with episodic discount risk; the
#     slippage curve is shallow but rises sharply near depeg. a=1e-4, b=0.45.
#   - Principal tokens (Pendle): illiquid secondary market, market makers
#     limited to a handful of vaults. Steeper curve. a=1e-3, b=0.65.
#   - Wrapped BTC variants: similar to mainline WBTC slippage. a=4e-4, b=0.55.
#   - Liquid staking tokens (wstETH, weETH): deep Curve/Balancer pools.
#     a=2e-4, b=0.52.
#   - Fallback (truly unknown asset): the historical generic curve.
ASSET_CLASS_PATTERNS = {
    # Order matters: more specific classes first.
    # Principal tokens (Pendle PT-/YT-) often contain a stablecoin substring
    # in their full symbol (e.g. "PT-apyUSD-18JUN2026"), so they must be
    # matched before stablecoin_synthetic to avoid misclassification.
    "principal_token": (["PT-", "YT-"], (1e-3, 0.65)),
    "wrapped_btc": (["LBTC", "tBTC", "BBTC", "swBTC"], (4e-4, 0.55)),
    "liquid_staking": (["wstETH", "weETH", "rsETH", "ezETH", "swETH"], (2e-4, 0.52)),
    "stablecoin_synthetic": (
        ["sUSDe", "sUSDS", "wsrUSD", "syrupUSDC", "AA_FalconXUSDC", "RLUSD",
         "USDtb", "USDe", "PYUSD", "FRAX"],
        (1e-4, 0.45),
    ),
}
FALLBACK_SLIPPAGE_GENERIC = (3e-4, 0.55)


# Minimum drawdown_p99 per asset class, used for forward-looking stress.
# Empirical p99 from short observation windows (1-3 months) under-estimates
# tail risk: most markets have not yet seen a major stress event in their
# observation window, so empirical p99 collapses to a few % even for assets
# that historically experienced 10-15% drawdowns.
#
# We therefore floor the empirical p99 at a class-specific minimum,
# calibrated against historical stress events (each justified below).
# When the empirical p99 exceeds this floor, the empirical value is used.
#
# Calibration sources:
#   - Stablecoin synthetic 5%: USDC depeg 2023-03-11 reached -8% trough;
#     5% is a conservative-but-realistic forward stress (BCBS 238 spirit:
#     stress should reflect adverse-but-plausible scenario).
#   - Liquid staking 8%: stETH discount 2022-05-12 reached -8% in <24h
#     during the 3AC/Celsius cascade (Lido OnChain Insights).
#   - Wrapped BTC 10%: BTC flash crash 2024-08-05 saw -12% intraday;
#     10% is the 24h equivalent stress consistent with that event.
#   - WETH/ETH 8%: ETH 24h drawdown during the same August 2024 event;
#     also matches the May 2021 Black Wednesday move.
#   - Principal token 15%: no equivalent historical event, but Pendle PT
#     secondary market is illiquid; a 15% mid-market discount during
#     stress is consistent with stress observed on similar yield-tokenised
#     instruments (synthetic receipts trade at 10-20% discounts when the
#     underlying yield product is questioned).
#   - Generic 8%: catch-all for unclassified collateral.
DRAWDOWN_P99_MIN_BY_CLASS = {
    "stablecoin_synthetic": 0.05,
    "liquid_staking": 0.08,
    "wrapped_btc": 0.10,
    "principal_token": 0.15,
    "weth": 0.08,
    "generic": 0.08,
}


def _classify_for_drawdown(symbol: str) -> str:
    """Return the asset class key for `DRAWDOWN_P99_MIN_BY_CLASS` lookup."""
    if not symbol:
        return "generic"
    sym_upper = symbol.upper()
    # Order matters: principal_token first to avoid USD-substring collision
    for pattern in ["PT-", "YT-"]:
        if pattern.upper() in sym_upper:
            return "principal_token"
    # Wrapped BTC family (includes cbBTC, WBTC, LBTC, tBTC, etc.)
    for pattern in ["LBTC", "TBTC", "BBTC", "SWBTC", "CBBTC", "WBTC", "BTC"]:
        if pattern in sym_upper:
            return "wrapped_btc"
    for pattern in ["WSTETH", "WEETH", "RSETH", "EZETH", "SWETH"]:
        if pattern in sym_upper:
            return "liquid_staking"
    for pattern in ["SUSDE", "SUSDS", "WSRUSD", "SYRUPUSDC", "AA_FALCONXUSDC",
                    "RLUSD", "USDTB", "USDE", "PYUSD", "FRAX", "SUSDAT",
                    "STCUSD", "STUSDS", "MSY", "MF-ONE"]:
        if pattern in sym_upper:
            return "stablecoin_synthetic"
    if sym_upper in {"WETH", "ETH"}:
        return "weth"
    return "generic"


def _classify_asset_for_slippage(symbol: str) -> tuple[float, float]:
    """Return (a, b) slippage parameters based on the symbol's asset class.

    Pattern-matches the symbol against known class signatures. Falls back to
    the generic curve if no class matches.
    """
    if not symbol:
        return FALLBACK_SLIPPAGE_GENERIC
    sym_upper = symbol.upper()
    for class_name, (patterns, params) in ASSET_CLASS_PATTERNS.items():
        for pattern in patterns:
            if pattern.upper() in sym_upper:
                return params
    return FALLBACK_SLIPPAGE_GENERIC


# ---------------------------------------------------------------------------
# Loan-asset USD conversion
# ---------------------------------------------------------------------------

# Hardcoded fallback prices for non-stable loan assets, used when the
# CoinGecko fetch fails (rate-limited, network down, etc.). Updated 2026-Q2.
LOAN_ASSET_USD_FALLBACK = {
    "WETH": 4500.0,
    "ETH": 4500.0,
    "WBTC": 98_000.0,
    "BTC": 98_000.0,
    "cbBTC": 98_000.0,
}

USD_STABLES = {
    "USDC", "USDT", "DAI", "PYUSD", "USDS", "FRAX", "USDe",
    "USDtb", "RLUSD", "TUSD", "USDD", "GHO", "crvUSD",
}


def _fetch_loan_asset_usd_price(symbol: str) -> float:
    """Return the USD price of 1 unit of `symbol`.

    Strategy:
      1. If symbol is a USD-pegged stable, return 1.0.
      2. Try CoinGecko free API (no auth required, 30 req/min rate limit).
      3. Fall back to hardcoded LOAN_ASSET_USD_FALLBACK with a warning.
    """
    if symbol.upper() in USD_STABLES:
        return 1.0

    # Map symbol to CoinGecko coin id
    coingecko_ids = {
        "WETH": "weth",
        "ETH": "ethereum",
        "WBTC": "wrapped-bitcoin",
        "BTC": "bitcoin",
        "cbBTC": "coinbase-wrapped-btc",
    }
    cg_id = coingecko_ids.get(symbol)
    if cg_id is None:
        # No CoinGecko mapping; try fallback
        fallback = LOAN_ASSET_USD_FALLBACK.get(symbol)
        if fallback is None:
            logger.warning(
                "No USD price available for %s; assuming 1.0 (will mislabel TVL)",
                symbol,
            )
            return 1.0
        logger.info("Using hardcoded fallback price for %s: $%.2f", symbol, fallback)
        return fallback

    try:
        import httpx
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            price = float(data[cg_id]["usd"])
            logger.info("CoinGecko price for %s: $%.2f", symbol, price)
            return price
    except Exception as e:
        fallback = LOAN_ASSET_USD_FALLBACK.get(symbol, 1.0)
        logger.warning(
            "CoinGecko price fetch failed for %s (%s); using fallback $%.2f",
            symbol, type(e).__name__, fallback,
        )
        return fallback


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_parquet(path: Path, schema_name: str) -> pd.DataFrame:
    """Load a Parquet file, return DataFrame. Logs row count."""
    if not path.exists():
        raise FileNotFoundError(f"Missing cache file: {path}. Run pipeline first.")
    df = pq.read_table(path).to_pandas()
    logger.info("Loaded %s: %d rows from %s", schema_name, len(df), path)
    return df


def _latest_per_market(df: pd.DataFrame, key: str = "market_id") -> pd.DataFrame:
    """Keep only the latest row per market (assumes block_number column)."""
    if "block_number" in df.columns:
        return df.sort_values("block_number").drop_duplicates(key, keep="last")
    if "block_ts" in df.columns:
        return df.sort_values("block_ts").drop_duplicates(key, keep="last")
    return df.drop_duplicates(key, keep="last")


# ---------------------------------------------------------------------------
# Per-field derivations
# ---------------------------------------------------------------------------

def _compute_drawdown_quantiles(prices: pd.Series, horizon_blocks: int = 7200) -> tuple[float, float]:
    """Empirical p50 and p99 of NEGATIVE log-returns over horizon_blocks.

    horizon_blocks=7200 ≈ 24 hours on Ethereum (12 second blocks).
    Returns (p50_drawdown, p99_drawdown), both in [0, 1].
    """
    if len(prices) < 50:
        # Insufficient series; conservative defaults
        return 0.02, 0.12

    arr = prices.to_numpy()
    log_arr = np.log(np.clip(arr, a_min=1e-12, a_max=None))

    # Stride to approximate horizon_blocks of separation. Our cadence is
    # typically 300 blocks = 1h, so stride 24 = 24h horizon.
    # Compute the actual stride from the series length and horizon.
    cadence_blocks = 300  # from config.sampling.oracle_price_period_blocks
    stride = max(1, horizon_blocks // cadence_blocks)

    if len(log_arr) <= stride:
        return 0.02, 0.12

    # Forward-looking 24h log-return: r_t = log(P_{t+stride}) - log(P_t)
    log_returns = log_arr[stride:] - log_arr[:-stride]
    # Drawdown = -min(0, log_return), i.e., positive value when price drops
    drawdowns = np.maximum(0.0, -log_returns)

    if len(drawdowns) == 0:
        return 0.02, 0.12

    p50 = float(np.quantile(drawdowns, 0.50))
    p99 = float(np.quantile(drawdowns, 0.99))
    # Clip to reasonable bounds; never zero (would break log calculations downstream)
    return max(p50, 0.001), max(p99, 0.005)


def _approximate_n_positions(events_borrow: pd.DataFrame, events_repay: pd.DataFrame, market_id: str) -> int:
    """Estimate the number of currently active borrowers in a market.

    Heuristic: count borrowers with a borrow event in the window but no
    repay-of-equal-or-greater amount after. For simplicity we count unique
    borrowers in the borrow event stream that ALSO appear less frequently
    in repay events.

    Production refinement: track per-borrower running balance via
    cumulative sum of share deltas.
    """
    if events_borrow.empty:
        return 0

    market_borrows = events_borrow[events_borrow["market_id"] == market_id]
    if market_borrows.empty:
        return 0

    unique_borrowers = market_borrows["on_behalf"].nunique()

    # If a market has many borrows but fewer unique borrowers, we are
    # likely seeing repeated activity from a small set. The unique count
    # is a tight upper bound on current active positions.
    return int(unique_borrowers)


def _approximate_avg_ltv(utilization: float, lltv: float) -> float:
    """Approximate the mean of the LTV distribution across active positions.

    Empirical calibration:
        On top Morpho Blue markets, position-level data (Block Analitica,
        Morpho explorer) shows that the mean LTV across active positions
        sits at approximately 0.60 to 0.70 times the LLTV in steady state.
        This reflects:
            - A majority of moderate leverage positions (LTV around 0.4-0.7
              of LLTV) typical of yield-aware borrowers.
            - A minority of aggressive carry traders pushing toward 0.85-0.95
              of LLTV (visible only in the right tail of the distribution).

        We use 0.65 * LLTV as the central estimate of the *mean*. The
        downstream `_profile_to_state` samples positions from a scaled
        Beta distribution with this mean, capturing the right-skew
        explicitly rather than collapsing it into a single point estimate.

        At low utilisation (< 0.40), we blend down because lightly-used
        markets may have a disproportionate share of "test" or stale
        positions at low LTV.

    Note:
        The previous heuristics in this codebase (U * LLTV * 0.85 and
        LLTV * 0.92) bracketed the true mean from below and above,
        respectively. Combined with the previous Normal LTV sampling in
        _profile_to_state, the LLTV * 0.92 setting produced spurious
        100% liquidation rates because the entire normal distribution
        was concentrated within 1-2 standard deviations of LLTV. Using
        a Beta distribution with mean 0.65 * LLTV resolves both issues.
    """
    avg_ltv = lltv * 0.65
    if utilization < 0.40:
        avg_ltv = avg_ltv * (0.60 + 0.40 * (utilization / 0.40))
    return float(np.clip(avg_ltv, 0.05, lltv - 1e-3))


def _fit_slippage(dex_slippage: pd.DataFrame, collateral_symbol: str) -> tuple[float, float]:
    """Fit the slippage curve `pi(V) = a * V^b` from DEX quote samples.

    Returns (a, b). Falls back to a class-based default if insufficient
    observations or fit fails. The class-based fallback differentiates
    between stablecoin synthetics, principal tokens, wrapped BTC variants,
    liquid staking tokens, and a generic catch-all (see
    `ASSET_CLASS_PATTERNS` for calibration rationale).
    """
    if dex_slippage.empty:
        a, b = _classify_asset_for_slippage(collateral_symbol)
        logger.info(
            "dex_slippage cache empty for %s; using class-based fallback (a=%g, b=%g)",
            collateral_symbol, a, b,
        )
        return a, b

    try:
        curve: SlippageCurve = fit_curve(dex_slippage, collateral_symbol, min_observations=10)
        return float(curve.a), float(curve.b)
    except (ValueError, KeyError) as e:
        a, b = _classify_asset_for_slippage(collateral_symbol)
        logger.info(
            "Slippage fit failed for %s (%s); using class-based fallback (a=%g, b=%g)",
            collateral_symbol, str(e).split(":")[0], a, b,
        )
        return a, b


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_market_profile(
    market_meta: dict,
    market_state_latest: dict,
    oracle_prices_market: pd.DataFrame,
    dex_slippage: pd.DataFrame,
    events_borrow: pd.DataFrame,
    events_repay: pd.DataFrame,
    loan_asset_usd_prices: dict[str, float] | None = None,
    positions_reconstructed_market: pd.DataFrame | None = None,
) -> MarketProfile:
    """Build a single MarketProfile from the per-market subset of cache data.

    Args:
        loan_asset_usd_prices: precomputed USD prices for non-stable loan assets,
            keyed by symbol. If None, prices are fetched on demand (slow).
        positions_reconstructed_market: per-borrower reconstructed positions for
            this market (from `enrich_positions.py`). When provided, the LTV
            distribution is taken empirically from these positions, replacing
            the parametric Beta distribution. n_positions is set to the count
            of active borrowers.
    """
    market_id = market_meta["market_id"]
    coll_symbol = market_meta["collateral_asset_symbol"]
    loan_symbol = market_meta["loan_asset_symbol"]
    lltv = float(market_meta["lltv"])
    # Disambiguate: two markets can share the same symbol pair but differ
    # in LLTV (Morpho intentionally lists multiple instances per pair to
    # offer different leverage tiers). We append the LLTV percentage to
    # the label to keep them distinct in the output table.
    label = f"{coll_symbol}/{loan_symbol} (LLTV={lltv:.2%})"

    # Extract latest state
    total_supply_assets = float(market_state_latest.get("total_supply_assets", 0.0))
    total_borrow_assets = float(market_state_latest.get("total_borrow_assets", 0.0))
    if total_supply_assets <= 0:
        raise ValueError(f"market {label}: total_supply_assets is zero or missing")
    utilization = min(1.0, max(0.0, total_borrow_assets / total_supply_assets))

    # Latest oracle price (raw IOracle.price() output, already normalised by
    # 1e36 + loan_dec - coll_dec, so it is in "loan asset units per collateral unit")
    if oracle_prices_market.empty:
        raise ValueError(f"market {label}: no oracle price observations")
    latest_price_row = oracle_prices_market.sort_values("block_number").iloc[-1]
    oracle_price = float(latest_price_row["price"])

    # USD conversion of total_supply.
    # When loan asset is USD-pegged, total_supply_assets is already in USD.
    # When loan asset is non-stable (WETH, WBTC), multiply by the loan-asset
    # USD price.
    if loan_symbol.upper() in USD_STABLES:
        total_supply_usd = total_supply_assets
    else:
        if loan_asset_usd_prices is not None and loan_symbol in loan_asset_usd_prices:
            loan_usd = loan_asset_usd_prices[loan_symbol]
        else:
            loan_usd = _fetch_loan_asset_usd_price(loan_symbol)
        total_supply_usd = total_supply_assets * loan_usd
        logger.info(
            "  %s: non-stable loan asset; total_supply=%.2f %s × $%.2f = $%.1fM",
            label, total_supply_assets, loan_symbol, loan_usd, total_supply_usd / 1e6,
        )

    # n_positions and avg_ltv from events
    # n_positions and avg_ltv: prefer empirical reconstruction when available
    if positions_reconstructed_market is not None and not positions_reconstructed_market.empty:
        n_positions = int(len(positions_reconstructed_market))
        # Volume-weighted mean LTV across reconstructed positions
        ltvs = positions_reconstructed_market["ltv"].to_numpy()
        weights = positions_reconstructed_market["net_borrow_assets"].to_numpy()
        if weights.sum() > 0:
            empirical_avg_ltv = float(np.average(ltvs, weights=weights))
        else:
            empirical_avg_ltv = float(np.mean(ltvs)) if len(ltvs) > 0 else _approximate_avg_ltv(utilization, lltv)
        # Cap below LLTV (positions above LLTV are typically already in liquidation queue)
        avg_ltv = float(np.clip(empirical_avg_ltv, 0.05, lltv - 1e-3))
        logger.debug(
            "Using empirical positions for %s: n=%d, weighted avg_ltv=%.3f",
            label, n_positions, avg_ltv,
        )
    else:
        n_positions = _approximate_n_positions(events_borrow, events_repay, market_id)
        avg_ltv = _approximate_avg_ltv(utilization, lltv)

    # Drawdown distribution from oracle price history.
    # The empirical p99 from a short observation window can severely under-
    # estimate tail risk if no major stress event has been observed. We
    # apply a class-specific minimum based on historical stress events
    # (see DRAWDOWN_P99_MIN_BY_CLASS for calibration).
    p50, p99_empirical = _compute_drawdown_quantiles(oracle_prices_market["price"])
    drawdown_class = _classify_for_drawdown(coll_symbol)
    p99_min = DRAWDOWN_P99_MIN_BY_CLASS.get(drawdown_class, 0.08)
    p99 = max(p99_empirical, p99_min)
    if p99 > p99_empirical:
        logger.info(
            "  %s: drawdown_p99 floored at %s class minimum %.1f%% "
            "(empirical was %.2f%%)",
            label, drawdown_class, p99 * 100, p99_empirical * 100,
        )

    # Slippage curve
    slippage_a, slippage_b = _fit_slippage(dex_slippage, coll_symbol)

    return MarketProfile(
        market_label=label,
        loan_symbol=loan_symbol,
        collateral_symbol=coll_symbol,
        total_supply_usd=total_supply_usd,
        utilization=utilization,
        n_positions=max(n_positions, 1),
        avg_ltv=avg_ltv,
        lltv=lltv,
        oracle_price=oracle_price,
        rate_at_target=DEFAULT_RATE_AT_TARGET,
        oracle_kind=str(market_meta.get("oracle_type", "unknown")),
        slippage_a=slippage_a,
        slippage_b=slippage_b,
        drawdown_p50=p50,
        drawdown_p99=p99,
    )


def build_all_profiles(
    cache_dir: Path,
) -> tuple[list[MarketProfile], dict[str, tuple[np.ndarray, np.ndarray]]]:
    """Read all cache files, build MarketProfile per market, and the empirical
    positions mapping (label -> (ltvs, borrow_weights)) when reconstructed
    positions are available. Returns (profiles, empirical_positions_by_label).
    """
    markets = _load_parquet(cache_dir / "markets.parquet", "markets")
    market_state = _load_parquet(cache_dir / "market_state.parquet", "market_state")
    oracle_prices = _load_parquet(cache_dir / "oracle_prices.parquet", "oracle_prices")

    # Optional caches
    try:
        dex_slippage = _load_parquet(cache_dir / "dex_slippage.parquet", "dex_slippage")
    except FileNotFoundError:
        dex_slippage = pd.DataFrame(columns=["collateral_symbol", "volume_native", "slippage_bps"])
        logger.warning("dex_slippage.parquet missing; slippage will use class-based fallback")

    try:
        events_borrow = _load_parquet(cache_dir / "events_borrow.parquet", "events_borrow")
    except FileNotFoundError:
        events_borrow = pd.DataFrame(columns=["market_id", "on_behalf"])

    try:
        events_repay = _load_parquet(cache_dir / "events_repay.parquet", "events_repay")
    except FileNotFoundError:
        events_repay = pd.DataFrame(columns=["market_id", "on_behalf"])

    # Reconstructed positions (optional). When present, this is used to derive
    # empirical avg_ltv and n_positions per market, replacing the Beta-scaled
    # parametric heuristic. Generated by `scripts/enrich_positions.py`.
    positions_reconstructed: pd.DataFrame | None
    pos_path = cache_dir / "positions_reconstructed.parquet"
    if pos_path.exists():
        positions_reconstructed = pq.read_table(pos_path).to_pandas()
        logger.info(
            "Loaded positions_reconstructed: %d positions across %d markets",
            len(positions_reconstructed),
            positions_reconstructed["market_id"].nunique(),
        )
    else:
        positions_reconstructed = None
        logger.info(
            "positions_reconstructed.parquet not found; using Beta-scaled "
            "parametric position distribution (run scripts/enrich_positions.py "
            "to enable empirical reconstruction)"
        )

    # Pre-fetch USD prices for non-stable loan assets (avoids N redundant
    # CoinGecko calls when multiple markets share the same loan asset).
    non_stable_loan_assets = {
        sym for sym in markets["loan_asset_symbol"].unique()
        if sym.upper() not in USD_STABLES
    }
    loan_asset_usd_prices: dict[str, float] = {}
    if non_stable_loan_assets:
        logger.info(
            "Pre-fetching USD prices for non-stable loan assets: %s",
            sorted(non_stable_loan_assets),
        )
        for sym in non_stable_loan_assets:
            loan_asset_usd_prices[sym] = _fetch_loan_asset_usd_price(sym)

    # Latest state per market
    state_latest = _latest_per_market(market_state).set_index("market_id")

    profiles: list[MarketProfile] = []
    for _, row in markets.iterrows():
        market_meta = row.to_dict()
        market_id = market_meta["market_id"]

        if market_id not in state_latest.index:
            logger.warning(
                "market %s/%s has no state observations; skipping",
                market_meta["collateral_asset_symbol"], market_meta["loan_asset_symbol"],
            )
            continue
        state_row = state_latest.loc[market_id].to_dict()

        oracle_subset = oracle_prices[oracle_prices["market_id"] == market_id].copy()

        # Subset of reconstructed positions for this market (if available)
        if positions_reconstructed is not None:
            positions_for_market = positions_reconstructed[
                positions_reconstructed["market_id"] == market_id
            ]
        else:
            positions_for_market = None

        try:
            profile = build_market_profile(
                market_meta=market_meta,
                market_state_latest=state_row,
                oracle_prices_market=oracle_subset,
                dex_slippage=dex_slippage,
                events_borrow=events_borrow,
                events_repay=events_repay,
                loan_asset_usd_prices=loan_asset_usd_prices,
                positions_reconstructed_market=positions_for_market,
            )
            profiles.append(profile)
            logger.info(
                "Built profile for %s: TVL=$%.1fM, util=%.1f%%, n_pos=%d, avg_ltv=%.3f",
                profile.market_label,
                profile.total_supply_usd / 1e6,
                profile.utilization * 100,
                profile.n_positions,
                profile.avg_ltv,
            )
        except (ValueError, KeyError) as e:
            logger.error(
                "Failed to build profile for %s: %s",
                market_meta.get("market_id", "?"), e,
            )
            continue

    # Build per-label mapping for downstream evaluators (assess_all_markets)
    empirical_positions_by_label: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    if positions_reconstructed is not None:
        # For each profile we built, find its market_id from the meta and
        # extract its positions
        meta_by_label = {
            f"{r['collateral_asset_symbol']}/{r['loan_asset_symbol']} (LLTV={float(r['lltv']):.2%})": r["market_id"]
            for _, r in markets.iterrows()
        }
        for profile in profiles:
            mid = meta_by_label.get(profile.market_label)
            if mid is None:
                continue
            subset = positions_reconstructed[positions_reconstructed["market_id"] == mid]
            if len(subset) >= 2:
                ltvs = subset["ltv"].to_numpy(dtype=float)
                weights = subset["net_borrow_assets"].to_numpy(dtype=float)
                empirical_positions_by_label[profile.market_label] = (ltvs, weights)
        logger.info(
            "Empirical positions available for %d/%d markets",
            len(empirical_positions_by_label), len(profiles),
        )

    return profiles, empirical_positions_by_label


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--cache-dir",
    default="data/cache",
    type=click.Path(exists=True, file_okay=False),
    help="Directory containing the cache Parquet files",
)
@click.option(
    "--output",
    "output_path",
    default="data/cache/market_profiles.json",
    type=click.Path(dir_okay=False),
    help="Output JSON file with serialised profiles",
)
@click.option(
    "--evaluate",
    is_flag=True,
    help="Also run the forward-looking risk evaluation and print the table",
)
@click.option(
    "--extreme",
    is_flag=True,
    help=(
        "Also run the extreme stress test (drawdown 25% + alpha 35%, "
        "calibrated on KelpDAO 2026 + USDC depeg 2023 hybrid). Shows "
        "which markets pass/fail under 99.5%-confidence stress."
    ),
)
@click.option(
    "--horizon-days",
    default=1,
    type=int,
    help=(
        "Stress test horizon in days. 1 (default) = canonical 24h LCR. "
        "7-30 = multi-day NSFR-style. Drawdown scaled by sqrt(horizon), "
        "runoff window scaled linearly."
    ),
)
def main(cache_dir: str, output_path: str, evaluate: bool, extreme: bool, horizon_days: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cache_root = Path(cache_dir)
    profiles, empirical_positions_by_label = build_all_profiles(cache_root)
    if not profiles:
        raise click.ClickException("No profiles built; check cache files")

    # Serialise to JSON for inspection
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        json.dump([asdict(p) for p in profiles], f, indent=2)
    logger.info("Wrote %d profiles to %s", len(profiles), output)

    # Optional: run the evaluation
    if evaluate:
        from morpho_stress.backtest.forward_looking import assess_all_markets

        logger.info(
            "Running forward-looking evaluation on %d markets (horizon=%d day%s)...",
            len(profiles), horizon_days, "s" if horizon_days != 1 else "",
        )
        results = assess_all_markets(
            profiles,
            n_mc_paths=200,
            empirical_positions_by_label=empirical_positions_by_label or None,
            horizon_days=horizon_days,
        )

        # Build a lookup so we can show TVL and utilization next to each row.
        profile_by_label: dict[str, MarketProfile] = {p.market_label: p for p in profiles}

        # Group by tier for the panorama view. Order: red, yellow, green-watch,
        # green-strong (most-to-least concerning).
        TIER_ORDER = ["red", "yellow", "green-watch", "green-strong"]
        TIER_LABELS = {
            "red": "RED (immediate attention)",
            "yellow": "YELLOW (under stress conditions)",
            "green-watch": "GREEN-WATCH (sound, monitor)",
            "green-strong": "GREEN-STRONG (robust)",
        }
        results_by_tier: dict[str, list] = {tier: [] for tier in TIER_ORDER}
        for r in results:
            tier = getattr(r, "severity_tier", r.severity_flag)
            if tier not in results_by_tier:
                results_by_tier[tier] = []
            results_by_tier[tier].append(r)

        # Sort within each tier by TVL descending (so panoramic view leads
        # with the most material markets in each band).
        for tier in results_by_tier:
            results_by_tier[tier].sort(
                key=lambda r: -(profile_by_label[r.market_label].total_supply_usd
                                if r.market_label in profile_by_label else 0.0)
            )

        # Header
        header_market = f"{'market':<42}"
        header_metrics = (
            f"{'TVL($M)':>9} {'util':>6} {'Pr(LCR<1)':>10} {'alpha':>7} "
            f"{'TTI(h)':>8} {'P[bd>0]':>9} {'p99 bd':>13} {'p99/TVL':>9}"
        )
        sep_width = len(header_market) + len(header_metrics) + 1

        print()
        print("=" * sep_width)
        print("FORWARD-LOOKING RISK PANORAMA — Morpho Blue (top markets)")
        print("=" * sep_width)

        for tier in TIER_ORDER:
            rows = results_by_tier.get(tier, [])
            if not rows:
                continue
            print()
            print(f"--- {TIER_LABELS[tier]} ({len(rows)} markets) ---")
            print(header_market + header_metrics)
            print("-" * sep_width)
            for r in rows:
                p = profile_by_label.get(r.market_label)
                tvl_m = (p.total_supply_usd / 1e6) if p else 0.0
                util_pct = (p.utilization * 100) if p else 0.0
                p99_tvl_pct = (
                    (r.p99_bad_debt_usd / p.total_supply_usd * 100)
                    if p and p.total_supply_usd > 0 else 0.0
                )
                tti_str = (
                    f"{r.time_to_illiquid_hours:.2f}"
                    if r.time_to_illiquid_hours != float("inf")
                    else "  inf"
                )
                print(
                    f"{r.market_label:<42}"
                    f"{tvl_m:>9.1f} {util_pct:>5.1f}% {r.pr_lcr_below_1:>9.2%} "
                    f"{r.alpha_calibrated:>7.2%} {tti_str:>8} {r.p_bad_debt_gt_0:>9.2%} "
                    f"${r.p99_bad_debt_usd:>11,.0f} {p99_tvl_pct:>8.3f}%"
                )

        # Summary
        print()
        print("=" * sep_width)
        n_by_tier = {tier: len(rows) for tier, rows in results_by_tier.items()}
        print(
            f"Summary: red={n_by_tier.get('red', 0)}  "
            f"yellow={n_by_tier.get('yellow', 0)}  "
            f"green-watch={n_by_tier.get('green-watch', 0)}  "
            f"green-strong={n_by_tier.get('green-strong', 0)}"
        )

        # Aggregate TVL by tier (informative for protocol-level narrative)
        tvl_by_tier = {
            tier: sum(
                profile_by_label[r.market_label].total_supply_usd
                for r in rows
                if r.market_label in profile_by_label
            ) / 1e6
            for tier, rows in results_by_tier.items()
        }
        total_tvl = sum(tvl_by_tier.values())
        if total_tvl > 0:
            print(
                f"TVL distribution: "
                f"red=${tvl_by_tier.get('red', 0):.0f}M ({tvl_by_tier.get('red', 0)/total_tvl*100:.1f}%)  "
                f"yellow=${tvl_by_tier.get('yellow', 0):.0f}M ({tvl_by_tier.get('yellow', 0)/total_tvl*100:.1f}%)  "
                f"green-watch=${tvl_by_tier.get('green-watch', 0):.0f}M ({tvl_by_tier.get('green-watch', 0)/total_tvl*100:.1f}%)  "
                f"green-strong=${tvl_by_tier.get('green-strong', 0):.0f}M ({tvl_by_tier.get('green-strong', 0)/total_tvl*100:.1f}%)"
            )
        print("=" * sep_width)

    if extreme:
        from morpho_stress.backtest.forward_looking import (
            EXTREME_ALPHA,
            EXTREME_DRAWDOWN,
            assess_all_markets_extreme,
        )

        logger.info(
            "Running extreme stress test (drawdown=%.0f%%, alpha=%.0f%%) on %d markets...",
            EXTREME_DRAWDOWN * 100, EXTREME_ALPHA * 100, len(profiles),
        )
        extreme_results = assess_all_markets_extreme(
            profiles,
            n_mc_paths=200,
            empirical_positions_by_label=empirical_positions_by_label or None,
        )

        # Build a lookup so we can show TVL next to each row
        profile_by_label_extreme: dict[str, MarketProfile] = {p.market_label: p for p in profiles}

        ext_header_market = f"{'market':<42}"
        ext_header_metrics = (
            f"{'TVL($M)':>9} {'survives':>10} {'LCR_ext':>9} "
            f"{'p99 bd':>13} {'p99/TVL':>9} {'#liq p99':>10}"
        )
        ext_sep_width = len(ext_header_market) + len(ext_header_metrics) + 1

        print()
        print("=" * ext_sep_width)
        print(
            f"EXTREME STRESS TEST — drawdown={EXTREME_DRAWDOWN:.0%}, "
            f"alpha={EXTREME_ALPHA:.0%} (KelpDAO 2026 + USDC depeg 2023 hybrid)"
        )
        print("=" * ext_sep_width)
        print(ext_header_market + ext_header_metrics)
        print("-" * ext_sep_width)

        n_survives = sum(1 for r in extreme_results if r.survives)
        n_fails = len(extreme_results) - n_survives
        tvl_survives = 0.0
        tvl_fails = 0.0

        for r in extreme_results:
            p = profile_by_label_extreme.get(r.market_label)
            tvl_m = (p.total_supply_usd / 1e6) if p else 0.0
            tvl_usd = p.total_supply_usd if p else 0.0
            if r.survives:
                tvl_survives += tvl_usd
            else:
                tvl_fails += tvl_usd
            survives_str = "PASS" if r.survives else "FAIL"
            print(
                f"{r.market_label:<42}"
                f"{tvl_m:>9.1f} {survives_str:>10} {r.lcr_extreme:>9.3f} "
                f"${r.p99_bad_debt_usd_extreme:>11,.0f} "
                f"{r.p99_bd_fraction_extreme*100:>8.2f}% {r.n_liquidated_extreme:>10}"
            )

        total_tvl_ext = tvl_survives + tvl_fails
        print("=" * ext_sep_width)
        print(
            f"Extreme summary: PASS={n_survives}/{len(extreme_results)} markets "
            f"(${tvl_survives/1e6:.0f}M, "
            f"{tvl_survives/total_tvl_ext*100 if total_tvl_ext > 0 else 0:.1f}% TVL)  "
            f"FAIL={n_fails}/{len(extreme_results)} markets "
            f"(${tvl_fails/1e6:.0f}M, "
            f"{tvl_fails/total_tvl_ext*100 if total_tvl_ext > 0 else 0:.1f}% TVL)"
        )
        print("=" * ext_sep_width)
        print(
            "Note: PASS = LCR >= 1.0 AND p99 bad-debt < 10% TVL under the "
            "extreme scenario."
        )


if __name__ == "__main__":
    main()
