"""Live 26-market evaluation driver for the v1.1 framework.

For every market available in ``data/cache/`` at the latest sampled block, the
driver computes the current report metrics:

1. ``alpha_star``: the largest 24-hour outflow fraction absorbed by available
   liquidity plus keeper-executable liquidation recoveries after re-marking the
   position book at the window-worst oracle price. Tiers: red below 10%, yellow
   below 30%, green at or above 30%.
2. ``time_to_illiquid`` at the market's drawdown-derived outflow proxy. This is
   a companion metric and does not determine the tier.
3. Two solvency readings: realised bad debt from the contract-aligned Monte
   Carlo engine and keeper-independent latent insolvency on stressed oracle
   terms.

The extreme test combines a class-aware collateral shock with a 35% outflow.
Liquidity and solvency failures are reported separately; latent insolvency is
not treated as realised protocol bad debt.

Inputs are produced by the scripts pipeline and include market state, oracle
prices, measured exit-depth curves and the reconstructed on-chain position book.
Outputs are ``docs/evaluation_results.csv`` and
``docs/evaluation_summary.json``. This script does not regenerate publication
prose; the assembled documentation is handled by the dedicated report scripts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from morpho_stress.backtest.liquidity_metrics import (
    calibrated_outflow_alpha,
    lcr_onchain_v03,
)
from morpho_stress.backtest.slippage_fit import fit_with_diagnostics
from morpho_stress.models.slippage import SlippageCurve
from morpho_stress.models.constants import BLOCK_TIME_SEC
from morpho_stress.scenarios import (
    EmpiricalDistribution,
    S1Config,
    S3Config,
    n_liquidated,
    run_monte_carlo,
    stress_s1,
    stress_s3,
    time_to_illiquid,
    total_bad_debt,
)
from morpho_stress.scenarios.liquidation import liquidation_incentive_factor
from morpho_stress.scenarios.state import MarketParams, MarketState, Position

log = logging.getLogger("run_evaluation")

# Exclusion-reason helpers: matured principal tokens exit via par redemption
# (no AMM depth to measure), permissioned wrappers have no public venue.
_MONTHS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
           "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
_PERMISSIONED_NOTES = {
    "AA_FalconXUSDC": "permissioned wrapper; no public exit venue to quote",
    "mF-ONE": "permissioned RWA wrapper; no public exit venue to quote",
}


def _pt_maturity(symbol: str):
    import datetime as _dt
    import re as _re
    m = _re.search(r"-(\d{2})([A-Z]{3})(\d{4})$", symbol or "")
    if not m or m.group(2) not in _MONTHS:
        return None
    return _dt.datetime(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1)),
                        tzinfo=_dt.timezone.utc)


def _no_curve_reason(symbol: str, fit_note: str) -> str:
    import datetime as _dt
    if symbol in _PERMISSIONED_NOTES:
        return _PERMISSIONED_NOTES[symbol]
    mat = _pt_maturity(symbol)
    if mat is not None and mat < _dt.datetime.now(_dt.timezone.utc):
        return (f"PT past maturity ({mat.date().isoformat()}): exit is par "
                f"redemption, AMM depth not applicable")
    return f"no slippage curve ({fit_note})"
HOURS_24 = int(24 * 3600 / BLOCK_TIME_SEC)
CACHE = Path("data/cache")


def _severity_alpha_star(alpha_star: float) -> str:
    """Tiers on the survival frontier: the maximum 24h outflow fraction the
    market absorbs (stressed liquid stock / supply). Thresholds anchor to the
    framework's own documented alpha calibration band (typical 0.10-0.30,
    cap 0.60): red below the bottom of the band, yellow inside it, green at
    or above its top."""
    return "red" if alpha_star < 0.10 else ("yellow" if alpha_star < 0.30 else "green")


def _severity_tti(tti_hours: float) -> str:
    return "red" if tti_hours < 12 else ("yellow" if tti_hours < 24 else "green")


def _severity_pbd(p: float) -> str:
    return "red" if p > 0.20 else ("yellow" if p > 0.05 else "green")


def _composite(sevs: list[str]) -> str:
    if "red" in sevs:
        return "red"
    if "yellow" in sevs:
        return "yellow"
    return "green"


def _col(df: pd.DataFrame, *candidates: str) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(
        f"none of {candidates} found; available columns: {list(df.columns)}"
    )


def _load_caches() -> dict[str, pd.DataFrame]:
    frames = {}
    for name in ("markets", "market_state", "oracle_prices", "dex_slippage"):
        path = CACHE / f"{name}.parquet"
        if not path.exists():
            sys.exit(f"[run_evaluation] missing {path}; run the fetch pipeline first")
        frames[name] = pd.read_parquet(path)
    pos_path = CACHE / "positions.parquet"
    frames["positions"] = pd.read_parquet(pos_path) if pos_path.exists() else None
    return frames


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-paths", type=int, default=200)
    ap.add_argument("--extreme-drawdown", type=float, default=0.25)
    ap.add_argument("--extreme-alpha", type=float, default=0.35)
    ap.add_argument("--min-fit-obs", type=int, default=8,
                    help="minimum slippage observations per collateral for the power-law fit")
    ap.add_argument("--allow-missing-positions", action="store_true",
                    help="degraded L1-only run for markets without reconstructed positions")
    ap.add_argument("--out-csv", default="docs/evaluation_results.csv")
    ap.add_argument("--out-json", default="docs/evaluation_summary.json")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("run_evaluation v5.1 (nature-aware exclusion reasons)")

    f = _load_caches()
    markets, mstate, oracle, slip = f["markets"], f["market_state"], f["oracle_prices"], f["dex_slippage"]
    positions = f["positions"]

    m_id = _col(markets, "market_id")
    ms_id = _col(mstate, "market_id")
    ms_block = _col(mstate, "block_number", "block")
    op_id = _col(oracle, "market_id")
    op_price = _col(oracle, "price", "oracle_price")
    op_block = _col(oracle, "block_number", "block")

    # one fitted slippage curve per collateral symbol (pipeline design)
    curves: dict[str, object] = {}
    fit_notes: dict[str, str] = {}
    slip_sym_col = _col(slip, "collateral_symbol")
    for sym in sorted(slip[slip_sym_col].unique()):
        sub = slip[(slip[slip_sym_col] == sym)
                   & (slip["volume_native"] > 0)]
        usable = sub[sub["slippage_bps"] > 0]
        if len(usable) < args.min_fit_obs:
            # Quoted but (near) flat curve: deep venue or premium pricing.
            # Build a conservative flat power-law from the largest observed
            # point instead of excluding a demonstrably liquid symbol.
            if len(sub) >= args.min_fit_obs:
                vol_max = float(sub["volume_native"].max())
                bps_max = float(max(sub["slippage_bps"].max(), 0.5))
                a = (bps_max / 1e4) / (vol_max ** 0.5) if vol_max > 0 else 1e-6
                curves[sym] = SlippageCurve(
                    asset_symbol=sym, a=a, b=0.5,
                    max_slippage=max(0.02, 10.0 * bps_max / 1e4),
                )
                fit_notes[sym] = f"flat fallback (max {bps_max:.1f} bps @ {vol_max:,.0f} native)"
                log.info("%s: %s", sym, fit_notes[sym])
            else:
                fit_notes[sym] = f"unusable quotes ({len(usable)}/{len(sub)} positive-bps rows)"
            continue
        try:
            res = fit_with_diagnostics(slip, sym, min_observations=args.min_fit_obs)
            curves[sym] = res.curve
            fit_notes[sym] = f"r2={res.r2:.2f}" if hasattr(res, "r2") else "ok"
        except Exception as e:  # noqa: BLE001 - fit must never kill the run
            fit_notes[sym] = f"fit failed: {e}"
            log.warning("%s: fit failed (%s)", sym, e)
    log.info("Fitted slippage curves for %d/%d collateral symbols",
             len(curves), slip[_col(slip, 'collateral_symbol')].nunique())

    rows, excluded, blocked = [], [], []
    for _, mk in markets.iterrows():
        mid = mk[m_id]
        label = f"{mk.get('collateral_asset_symbol', '?')}/{mk.get('loan_asset_symbol', '?')}"

        st = mstate[mstate[ms_id] == mid]
        pr = oracle[oracle[op_id] == mid]
        if st.empty:
            excluded.append((mid, label, "no market_state rows")); continue
        if pr.empty:
            excluded.append((mid, label, "no oracle price series (oracle interface not supported this window)")); continue
        csym = mk.get("collateral_asset_symbol")
        if csym not in curves:
            excluded.append((mid, label, _no_curve_reason(csym, fit_notes.get(csym, 'no quotes')))); continue
        curve = curves[csym]

        snap = st.loc[st[ms_block].idxmax()]
        block = int(snap[ms_block])
        # Restrict the oracle series to the market_state sampling window:
        # the oracle fetcher samples from its own (older) range start up to
        # head, and feeding months of stale volatility into a current 24h
        # stress inflates both worst_price and the alpha calibration.
        win_lo = int(st[ms_block].min())
        pr_win = pr[pr[op_block] >= win_lo] if op_block in pr.columns else pr
        if pr_win.empty:
            pr_win = pr
        prices = pr_win.sort_values(op_block)[op_price].to_numpy(dtype=float)
        latest_price = float(prices[-1])
        worst_price = float(prices.min())

        pos_tuple: tuple[Position, ...] = ()
        pos_note = ""
        if positions is not None:
            pm = positions[positions[_col(positions, "market_id")] == mid]
            if not pm.empty:
                pblock_col = _col(positions, "block_number", "block")
                pblocks = pm[pblock_col]
                use_block = int(pblocks[pblocks <= block].max()) if (pblocks <= block).any() else int(pblocks.max())
                sel = pm[pm[pblock_col] == use_block]
                pos_tuple = tuple(
                    Position(
                        borrower=str(r[_col(positions, "borrower")]),
                        collateral=float(r["collateral"]),
                        borrow_shares=float(r["borrow_shares"]),
                    )
                    for _, r in sel.iterrows()
                    if float(r["borrow_shares"]) > 0 or float(r["collateral"]) > 0
                )
                if use_block != block:
                    pos_note = f"positions@{use_block} vs state@{block}"
        if not pos_tuple:
            if args.allow_missing_positions:
                pos_note = "NO POSITIONS (degraded: L1-only, no recovery, no MC bad debt)"
            else:
                blocked.append((mid, label)); continue

        params = MarketParams(
            market_id=mid,
            loan_decimals=int(mk[_col(markets, "loan_asset_decimals", "loan_decimals")]),
            collateral_decimals=int(mk[_col(markets, "collateral_asset_decimals", "collateral_decimals")]),
            lltv=float(mk["lltv"]) if float(mk["lltv"]) <= 1 else float(mk["lltv"]) / 1e18,
            fee=float(snap["fee"]) if "fee" in snap.index and pd.notna(snap.get("fee")) else 0.0,
        )
        total_coll = float(snap.get("total_collateral") or 0.0)
        if total_coll <= 0 and pos_tuple:
            total_coll = float(sum(p.collateral for p in pos_tuple))
        state = MarketState(
            params=params,
            block=block,
            block_ts=int(pd.Timestamp(snap[_col(mstate, "block_ts", "timestamp")]).timestamp())
            if "block_ts" in snap.index or "timestamp" in snap.index else 0,
            total_supply_assets=float(snap[_col(mstate, "total_supply_assets", "supply_assets")]),
            total_supply_shares=float(snap[_col(mstate, "total_supply_shares", "supply_shares")]),
            total_borrow_assets=float(snap[_col(mstate, "total_borrow_assets", "borrow_assets")]),
            total_borrow_shares=float(snap[_col(mstate, "total_borrow_shares", "borrow_shares")]),
            total_collateral=total_coll,
            oracle_price=latest_price,
            rate_at_target=float(snap["rate_at_target"]) if "rate_at_target" in snap.index and pd.notna(snap.get("rate_at_target")) else 0.04,
            positions=pos_tuple,
        )

        # Embedded book diagnostics: decide between "genuinely conservative
        # book" and "collateral scaling bug" without a separate script.
        tb, ts_ = state.total_borrow_assets, state.total_borrow_shares
        b_vec = [pp.borrow_assets(tb, ts_) for pp in pos_tuple]
        c_val = sum(pp.collateral for pp in pos_tuple) * latest_price
        book_ltv = (sum(b_vec) / c_val) if c_val > 0 else float("nan")
        ltvs = [b / (pp.collateral * latest_price)
                for pp, b in zip(pos_tuple, b_vec) if pp.collateral > 0 and b > 0]
        max_ltv_obs = max(ltvs) if ltvs else float("nan")
        n_dust_baddebt = sum(1 for pp, b in zip(pos_tuple, b_vec)
                             if b > 0 and pp.collateral <= 0)
        wd = (latest_price - worst_price) / latest_price if latest_price > 0 else 0.0
        log.info("%-28s window_dd(latest->worst)=%.1f%% book_LTV=%.3f max_pos_LTV=%.3f dust_baddebt_pos=%d",
                 label, wd * 100, book_ltv, max_ltv_obs, n_dust_baddebt)
        if book_ltv == book_ltv and book_ltv < 0.02:
            log.warning("%s: book LTV %.4f is implausibly low; SUSPECT collateral scaling from the API",
                        label, book_ltv)

        alpha = calibrated_outflow_alpha(prices)

        # Criterion 1 on the STRESSED state: under the 24h stress the oracle
        # tracks the worst observed price, positions that cross LLTV at that
        # price become liquidatable and deliver recoveries (oracle-lag is the
        # scenario of criterion 3's shocks, not of this stock measure).
        state_stress = state.replace(oracle_price=worst_price)
        lcr, comps = lcr_onchain_v03(state_stress, worst_price, curve, alpha)
        # Survival frontier: LSR x alpha = stressed HQLA-like stock / supply,
        # i.e. the largest 24h outflow fraction the market can absorb. This is
        # the primary, alpha-independent discriminator; the empirical alpha
        # stays reported as the window's stress marker.
        alpha_star = lcr * alpha
        sev1 = _severity_alpha_star(alpha_star)

        traj = stress_s1(state, S1Config(alpha=alpha, duration_blocks=HOURS_24, horizon_blocks=HOURS_24))
        tti = time_to_illiquid(traj)
        tti_h = tti * BLOCK_TIME_SEC / 3600 if tti is not None else float("inf")
        sev2 = _severity_tti(tti_h)

        dds = []
        for i in range(len(prices) - 24):
            peak = prices[i]
            if peak <= 0:
                continue
            dds.append(max(0.0, (peak - prices[i:i + 24].min()) / peak))
        dist = EmpiricalDistribution(observations=np.array(dds) if dds else np.array([0.05, 0.10, 0.20, 0.30]))
        mc = run_monte_carlo(
            initial_state=state,
            distribution=dist,
            scenario_fn=lambda s, d: stress_s3(
                s, S3Config(drawdown=float(d), dt_blocks=HOURS_24, horizon_blocks=HOURS_24, shape="instant"), curve
            ),
            metric_fns={"bad_debt": total_bad_debt, "n_liq": lambda t: float(n_liquidated(t))},
            n_paths=args.n_paths,
            seed=42,
        )
        bd = mc["bad_debt"]
        p_bd = float((bd.samples > 0).mean())
        supply = state.total_supply_assets
        bd_p99_pct = float(bd.p99) / supply * 100 if supply > 0 else 0.0

        # Analytic MC companion, immune to the keeper-strike regime: latent
        # insolvency (Morpho.sol exhaustion condition) under the SAME empirical
        # drawdown distribution. b and c are position vectors; a draw dd makes
        # position i insolvent for b_i > c_i * P*(1-dd) / LIF.
        lif = liquidation_incentive_factor(params.lltv)
        b_arr = np.array(b_vec)
        c_arr = np.array([pp.collateral for pp in pos_tuple])
        draws = np.random.default_rng(42).choice(
            dist.observations, size=args.n_paths, replace=True)
        insolv_draws = np.array([
            np.maximum(0.0, b_arr - c_arr * latest_price * (1 - dd) / lif).sum()
            for dd in draws
        ])
        p_insolv = float((insolv_draws > 0).mean())
        insolv_p99_pct = float(np.quantile(insolv_draws, 0.99)) / supply * 100 if supply > 0 else 0.0
        sev3 = _severity_pbd(max(p_bd, p_insolv))

        # Class-aware extreme drawdown: a 25% shock is meaningless for
        # redemption-arbitraged correlated pairs (wstETH/WETH etc.) whose
        # window-worst 24h drawdown is near zero; cap the shock at 3x the
        # worst observed, floored at 5%, for those markets.
        worst_dd = max(dds) if dds else 0.0
        dd_x = args.extreme_drawdown if worst_dd >= 0.03 else min(
            args.extreme_drawdown, max(0.05, 3.0 * worst_dd)
        )
        price_x = latest_price * (1 - dd_x)
        state_x = state.replace(oracle_price=price_x)
        lcr_x, _ = lcr_onchain_v03(state_x, price_x, curve, args.extreme_alpha)

        # Realized bad debt via the engine (subject to the keeper-strike
        # regime under deep slippage)...
        traj_x = stress_s3(
            state, S3Config(drawdown=dd_x, dt_blocks=HOURS_24, horizon_blocks=HOURS_24, shape="instant"), curve
        )
        bd_x_pct = total_bad_debt(traj_x) / supply * 100 if supply > 0 else 0.0
        # ...and DIRECT latent insolvency, immune to keeper strikes: debt not
        # covered by collateral on stressed oracle terms (Morpho.sol
        # exhaustion condition), whether or not any keeper executes.
        insolvency_x = sum(
            max(0.0, p.borrow_assets(state.total_borrow_assets, state.total_borrow_shares)
                - p.collateral * price_x / lif)
            for p in pos_tuple
        )
        insolvency_x_pct = insolvency_x / supply * 100 if supply > 0 else 0.0
        extreme_illiq_fail = lcr_x < 1.0
        extreme_insolv_fail = insolvency_x_pct > 10.0
        extreme_fail = extreme_illiq_fail or extreme_insolv_fail

        rows.append({
            "market_id": mid, "market": label, "block": block,
            "supply_assets": supply, "utilization": state.utilization,
            "n_positions": len(pos_tuple), "alpha": alpha,
            "alpha_star": alpha_star,
            "lsr24": lcr, "tti_hours": tti_h, "p_bad_debt": p_bd,
            "p_insolvency": p_insolv, "insolvency_p99_pct": insolv_p99_pct,
            "bad_debt_p99_pct": bd_p99_pct, "severity": _composite([sev1, sev2, sev3]),
            "extreme_drawdown_used": dd_x,
            "lsr24_extreme": lcr_x, "bad_debt_extreme_realized_pct": bd_x_pct,
            "insolvency_extreme_pct": insolvency_x_pct,
            "extreme_illiq_fail": extreme_illiq_fail,
            "extreme_insolv_fail": extreme_insolv_fail,
            "extreme_fail": extreme_fail, "notes": pos_note,
        })
        log.info("%-28s a*=%.0f%% LSR=%.2f TTI=%s P(bd)=%.0f%% sev=%-6s extreme(dd=%.0f%%)=%s insolv=%.1f%% %s",
                 label, alpha_star * 100, lcr, ("inf" if tti_h == float("inf") else f"{tti_h:.1f}h"),
                 max(p_bd, p_insolv) * 100, rows[-1]["severity"], dd_x * 100,
                 "FAIL" if extreme_fail else "pass", insolvency_x_pct, pos_note)

    if blocked:
        names = "\n  ".join(f"{l} ({m})" for m, l in blocked)
        sys.exit(
            f"[run_evaluation] {len(blocked)} markets have no reconstructed positions:\n  {names}\n"
            "positions.parquet is built by scripts/enrich_positions.py from the events layer\n"
            "(scripts/fetch_events.py). Fix/fetch events, run enrich_positions.py, then re-run.\n"
            "Or pass --allow-missing-positions for a degraded L1-only evaluation."
        )

    df = pd.DataFrame(rows).sort_values("supply_assets", ascending=False)
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out_csv, index=False)

    tv = df["supply_assets"].sum()
    summary = {
        "engine": "v1.1",
        "alpha_star_median": float(df["alpha_star"].median()),
        "alpha_star_min": float(df["alpha_star"].min()),
        "markets_evaluated": int(len(df)),
        "markets_excluded": [{"market_id": m, "market": l, "reason": r} for m, l, r in excluded],
        "tiers": df["severity"].value_counts().to_dict(),
        "extreme_failures": int(df["extreme_fail"].sum()),
        "extreme_illiquidity_failures": int(df["extreme_illiq_fail"].sum()),
        "extreme_insolvency_failures": int(df["extreme_insolv_fail"].sum()),
        "extreme_fail_tvl_share_pct": float(df.loc[df["extreme_fail"], "supply_assets"].sum() / tv * 100) if tv else 0.0,
        "extreme_params": {"drawdown": args.extreme_drawdown, "alpha": args.extreme_alpha},
        "n_paths": args.n_paths,
    }
    Path(args.out_json).write_text(json.dumps(summary, indent=2))

    print(df[["market", "supply_assets", "alpha", "alpha_star", "lsr24", "tti_hours",
              "p_insolvency", "insolvency_p99_pct", "severity", "extreme_drawdown_used",
              "lsr24_extreme", "insolvency_extreme_pct",
              "extreme_illiq_fail", "extreme_insolv_fail"]]
          .to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print(f"\nTiers: {summary['tiers']} | extreme: {summary['extreme_illiquidity_failures']} illiquidity fails, "
          f"{summary['extreme_insolvency_failures']} insolvency fails "
          f"({summary['extreme_fail_tvl_share_pct']:.1f}% of evaluated supply fails at least one leg)")
    for m, l, r in excluded:
        print(f"EXCLUDED {l}: {r}")
    print(f"\nWrote {args.out_csv} and {args.out_json}")


if __name__ == "__main__":
    main()
