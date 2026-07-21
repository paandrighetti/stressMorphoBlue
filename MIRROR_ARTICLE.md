> **DRAFT. Pre-flight: fetch aggregator depth for exotic collateral (`python scripts/fetch_agg_quotes.py --source kyberswap`, raise `--pause-s` on 429) or accept the reduced evaluated set; then re-run `run_evaluation.py`, `generate_report_tables.py --snapshot-date <state date>`, `assemble_docs.py`; verify the injected figures; delete this banner.**

## Why this matters

Decentralised-finance lending protocols hold tens of billions of dollars of deposits, and their fragility under stress is theoretically established (Chiu, Ozdenoren, Yuan & Zhang, BIS Working Paper 1062, 2023). Yet most public risk reports for these protocols transpose Basel concepts informally, without explicit pass-or-fail criteria, and without a reproducible backtest against historical events.

This work formalises the transposition for **Morpho Blue**, the non-custodial lending protocol with isolated markets and immutable parameters. We adapt the **Liquidity Coverage Ratio** defined by the Basel Committee on Banking Supervision in BCBS 238 (2013) and apply it to live on-chain data.

The full source code, test suite, and reproducible event fixtures are open-source. All tests pass; the 26-market evaluation is computed from a live mainnet snapshot. A separate forward-looking module ships as an explicitly synthetic v0 demonstration and feeds none of the figures.

---

## What we measure

For each market, on its **actual onchain position book**, three criteria in the spirit of BCBS 238:

1. **Survival frontier (alpha\*)**, the primary metric: the largest 24-hour outflow fraction the market absorbs from instantaneous liquidity plus stress-liquidatable recoveries, with the oracle re-marked at the window-worst price and keeper executability enforced. Tiers anchor to the framework's documented calibration band: red below 10%, yellow below 30%, green at or above 30%.
2. **Time-to-illiquid**: hours before instant liquidity is exhausted at the window-calibrated outflow rate.
3. **Solvency, two readings**: realized bad debt through the contract-faithful engine (structurally near zero under keeper strikes), and latent insolvency, debt not covered by collateral on stressed oracle terms, computed analytically and independent of keeper behaviour.

The v1.0 four-tier scheme is retired; the empirical outflow alpha of each market's own window is reported as a stress marker, not as the verdict.

---

## Calibration: against history, not vibes

The framework is anchored on three historical stress events:

- **KelpDAO collateral exploit** (April 2026), the primary anchor.
- **USDC depeg** (March 2023), with -8% trough, ~25% day-one Aave outflow.
- **Staked-Ether discount episode** (May 2022), -8% trough over multiple days.

Two events PASS the framework's pre-event detection criteria. The third (stETH 2022) FAILs honestly: the framework is a 24-hour survival test (LSR-24) and the stETH episode was a multi-day repricing rather than an acute liquidity stress. We report this failure rather than retrofitting parameters to make it pass.

**Base stress is each market's own recent window** (v1.1): the worst 24-hour oracle print re-marks the state, and the outflow alpha derives from the market's empirical drawdown distribution (with a documented discontinuity at the 5% large-holder trigger, which is precisely why the survival frontier, not alpha, is the verdict). Class-aware floors survive only in the **extreme test**: 25% drawdown for volatile collateral, capped at three times the window-worst move (floored at 5%) for redemption-arbitraged pairs, with a 35% outflow anchored on the KelpDAO and USDC-depeg episodes.

---

## Methodology in one paragraph

We fetch the live position book from the Morpho API (per-market borrow-share coverage checked against onchain state), fit exit-depth curves from quoted liquidity (Uniswap V3 quoter for majors; keyless CoW Protocol and KyberSwap quotes, rebased on the smallest executed size, for yield-bearing collateral; Pendle-router curves for principal tokens), re-mark each market at its window-worst oracle print, and ask one question: how large a 24-hour outflow does the market absorb, counting only instantaneous liquidity and recoveries from positions that actually become liquidatable, executable by a rational keeper at the aggregate slippage? A Monte Carlo over the market's own drawdown distribution adds the solvency leg, split into realized bad debt (Morpho.sol exhaustion semantics) and latent insolvency (keeper-independent). An extreme scenario with class-aware shocks and 35% outflows closes the loop with a two-leg pass-or-fail.

---

## Findings

<!-- BEGIN GENERATED: mirror_findings -->
As of 2026-07-16 (state block 25,545,086), across 24 evaluated markets, the survival frontier, the largest 24-hour outflow a market absorbs from instantaneous liquidity plus stress-liquidatable recoveries, ranges from 1.0% (AA_FalconXUSDC/USDC) to 41.1% (PT-reUSD-25JUN2026/USDC), median 10.7%. The binding variable is utilisation, not collateral class.

The second axis is the mirror image: under a class-aware extreme scenario, 20 of 24 markets fail on liquidity while 0 fail on solvency; latent insolvency stays below 0.7% of supply everywhere. Position books are conservative; liabilities are not.

Versus v1.0: the earlier yellow/green tiering was an artefact of a structural double-count (recoveries in both numerator and netted outflows, correction C6) compounded by non-callable healthy debt counted as monetisable (C4). The v1.1 engine removes both and reports what remains: a liquidity question that rate-driven replenishment, not modelled in this version, answers in practice.
<!-- END GENERATED: mirror_findings -->

Curator-level analysis of MetaMorpho vault allocations, scoring how vault deposits distribute across the tiers above, follows in a separate post.

---

## Honest limitations

We treat known limits as data:

- **No rate-driven replenishment.** The withdrawal run is mechanical; borrowers repaying into a spiking rate curve, the main real-world stabiliser, is not modelled. Survival frontiers are lower bounds in that respect.
- **Keeper strike is all-or-none.** If the aggregate resale of the eligible batch is unprofitable at the aggregate slippage, no liquidation executes. Realized bad debt near zero under stress is a regime, not a comfort; latent insolvency is the number to read.
- **The alpha calibration is discontinuous** at its 5% large-holder trigger (two otherwise similar markets can carry very different markers); the survival frontier is the discontinuity-free verdict.
- **Aggregator depth is conservative for instantly-redeemable wrappers** (arbitrageurs can mint and redeem at net asset value); for cooldown wrappers such as sUSDe, the measured curve is the 24-hour exit.
- **Single snapshot, Ethereum mainnet only, oracle integrity assumed.** Oracle manipulation is a distinct attack surface, not covered here.
- **Backtest fixtures are partly synthetic reconstructions** (recorded aggregates, synthetic splits), documented as such; the forward panorama, by contrast, evaluates the actual book.

---

## Reproducibility

```bash
git clone https://github.com/paandrighetti/stressMorphoBlue
cd stressMorphoBlue && uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
PYTHONPATH=src pytest tests/        # 146 tests, ~2 minutes

# figures chain (from cached data to the tables in this article)
python scripts/run_evaluation.py
python scripts/generate_report_tables.py
python scripts/assemble_docs.py
PYTHONPATH=src python scripts/enrich_forward_looking.py --evaluate --extreme
```

The Dune dashboard with live TVL, top markets, and liquidation flows is at:
https://dune.com/bandulf/morpho-blue-liquidity-stress

---

## What this work is not

Not investment advice. Not a security audit. Not a recommendation to deposit on or borrow from any Morpho Blue lending market. The author has no affiliation with Morpho Labs, MetaMorpho vault curators, or any protocol mentioned, beyond public usage.

The contribution is methodological: a reproducible, falsifiable risk framework grounded in regulatory practice and applied to live data, with explicit limitations.

---

*Source: github.com/paandrighetti/stressMorphoBlue*
