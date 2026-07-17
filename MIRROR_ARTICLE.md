> **DRAFT. Regenerate every figure and table with the v1.1 engine before publishing (docs/MODEL_CORRECTIONS.md).**

## Why this matters

Decentralised-finance lending protocols hold tens of billions of dollars of deposits, and their fragility under stress is theoretically established (Chiu, Ozdenoren, Yuan & Zhang, BIS Working Paper 1062, 2023). Yet most public risk reports for these protocols transpose Basel concepts informally, without explicit pass-or-fail criteria, and without a reproducible backtest against historical events.

This work formalises the transposition for **Morpho Blue**, the non-custodial lending protocol with isolated markets and immutable parameters. We adapt the **Liquidity Coverage Ratio** defined by the Basel Committee on Banking Supervision in BCBS 238 (2013) and apply it to live on-chain data.

The full source code, test suite, and reproducible event fixtures are open-source. All tests pass; the 26-market evaluation is computed from a live mainnet snapshot. A separate forward-looking module ships as an explicitly synthetic v0 demonstration and feeds none of the figures.

---

## What we measure

For each market, three pass-or-fail criteria, all sourced from the spirit of BCBS 238:

1. **Continuous liquidity coverage**: probability that the liquid stock falls below stressed outflows under a 24-hour scenario, denoted Pr(LSR-24 < 1). The metric is LCR-inspired; BCBS 238 itself defines a 30-day horizon.
2. **Time-to-illiquid**: hours before instant liquidity is exhausted under a calibrated outflow rate.
3. **Bad-debt magnitude**: 99th-percentile bad debt expressed as a fraction of Total Value Locked.

A market is `red` when any single component reaches red severity; `yellow` for stress-band conditions; `green-watch` for sound-but-monitor; `green-strong` for fully robust.

---

## Calibration: against history, not vibes

The framework is anchored on three historical stress events:

- **KelpDAO collateral exploit** (April 2026), the primary anchor.
- **USDC depeg** (March 2023), with -8% trough, ~25% day-one Aave outflow.
- **Staked-Ether discount episode** (May 2022), -8% trough over multiple days.

Two events PASS the framework's pre-event detection criteria. The third (stETH 2022) FAILs honestly: the framework is a 24-hour survival test (LSR-24) and the stETH episode was a multi-day repricing rather than an acute liquidity stress. We report this failure rather than retrofitting parameters to make it pass.

**Class-floored drawdowns** for forward-looking stress, calibrated per asset class against the events above:

- Stablecoin synthetics: 5%
- Liquid staking tokens: 8%
- Wrapped Bitcoin variants: 10%
- Pendle principal tokens: 15%
- Wrapped Ether: 8%

These minima override the empirical 99th-percentile when the observed history is shorter than the structural risk of the asset class.

---

## Methodology in one paragraph

For each market we run two stress scenarios in parallel rather than cumulating both stresses in one path. **Scenario A** combines a class-floored 99th-percentile drawdown with a moderate outflow alpha. **Scenario B** combines a typical drawdown with an amplified outflow alpha (20% to 30%, calibrated on KelpDAO and the USDC depeg). The reported LCR is the worst of the two; the bad-debt distribution comes from a Monte Carlo over the empirical drawdown distribution. Position-level loan-to-values are sampled from a Beta distribution with mean 0.65 × LLTV, capturing the right-skewed observation that most borrowers are moderately leveraged with an aggressive minority near the liquidation threshold.

---

## Findings

<!-- BEGIN GENERATED: mirror_findings -->
Across 11 evaluated markets, the survival frontier, the largest 24-hour outflow a market absorbs from instantaneous liquidity plus stress-liquidatable recoveries, ranges from 9.8% (weETH/PYUSD) to 21.8% (cbBTC/PYUSD), median 10.9%. The binding variable is utilisation, not collateral class.

The second axis is the mirror image: under a class-aware extreme scenario, 11 of 11 markets fail on liquidity while 0 fail on solvency; latent insolvency stays below 0.7% of supply everywhere. Position books are conservative; liabilities are not.

Versus v1.0: the earlier yellow/green tiering was an artefact of a structural double-count (recoveries in both numerator and netted outflows, correction C6) compounded by non-callable healthy debt counted as monetisable (C4). The v1.1 engine removes both and reports what remains: a liquidity question that rate-driven replenishment, not modelled in this version, answers in practice.
<!-- END GENERATED: mirror_findings -->

## Findings, MetaMorpho curator discipline

> *(v1.0 enrichment figures; regenerate or defer to a follow-up before publishing.)*

Beyond the per-market view, we apply the tier classification to score the **discipline of the top 20 MetaMorpho vaults** by Total Value Locked. The score is a TVL-weighted exposure to severity tiers (red=4, yellow=2, green-watch=1, green-strong=0). A score of 0 is fully conservative; 2 is significant yellow exposure; above 2 warrants curator-side review.

The result is a **structural finding** rather than a quality ranking: **the four largest USDC-asset vaults converge at a score of approximately 2.0**, reflecting near-exclusive allocation to mainstream BTC/ETH-collateral markets that the framework classifies as yellow.

| Vault | TVL ($M) | Score | yellow% allocation |
|---|---|---|---|
| Gauntlet USDC Prime | 150.9 | 2.00 | 100% |
| Steakhouse USDC | 129.4 | 1.94 | 96.8% |
| Vault Bridge USDC | 48.9 | 2.00 | 100% |
| Hakutora USDC | 16.4 | 2.00 | 100% |

This is not curator imprudence: it is that **the USDC vault product structurally concentrates the protocol's material tail risk** in a small number of mainstream markets where the bulk of DeFi USDC yield originates. The risk is not idiosyncratic to any one curator. By contrast, RLUSD-asset and PYUSD-asset vaults (Sentora) achieve scores below 1.0 by diversifying across green-strong synthetic-stablecoin markets.

The finding is reproducible end-to-end: `python scripts/fetch_metamorpho_vaults.py --top 20`.

---

## Honest limitations

We treat known failures as data:

- **3 corner cases require investigation.** stcUSD/USDT passes the extreme test with zero liquidations, possibly because the synthetic price feed is yield-adjusted and partially insulated from the drawdown injection. LBTC/PYUSD passes with three liquidations and zero bad debt, clean closure rather than insolvency. msY/USDC passes nominal-strong but fails extreme, likely small-sample variance in the position distribution.
- **Position-level reconstruction is approximate.** We use a parametric Beta with mean 0.65 × LLTV. A production deployment should reconstruct actual position-level LTVs from collateral and borrow events.
- **Maximal-extractable-value and liquidator-competition effects are not modelled.** Liquidations are atomic at modelled DEX prices; in reality, gas-price competition can leave some liquidations unprofitable.
- **The continuous LCR criterion returns Pr(LCR < 1) = 0% across all 26 markets.** This is plausibly a positive signal: under BCBS-aligned stress with healthy overcollateralisation, no Morpho Blue market we analysed approaches the LCR threshold of 1. But it could also signal that the LCR criterion as parameterised is insufficiently sensitive to extreme tail risks; the extreme stress test is the discriminating signal.

---

## Reproducibility

```bash
git clone https://github.com/YungBandulf/stressMorphoBlue
cd stressMorphoBlue && uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
PYTHONPATH=src pytest tests/        # 145 tests, ~2 minutes
PYTHONPATH=src python scripts/enrich_forward_looking.py --evaluate --extreme
```

The Dune dashboard with live TVL, top markets, and liquidation flows is at:
https://dune.com/bandulf/morpho-blue-liquidity-stress

---

## What this work is not

Not investment advice. Not a security audit. Not a recommendation to deposit on or borrow from any Morpho Blue lending market. The author has no affiliation with Morpho Labs, MetaMorpho vault curators, or any protocol mentioned, beyond public usage.

The contribution is methodological: a reproducible, falsifiable risk framework grounded in regulatory practice and applied to live data, with explicit limitations.

---

*Source: github.com/YungBandulf/stressMorphoBlue*
