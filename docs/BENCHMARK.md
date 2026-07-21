# Benchmark vs incumbent risk frameworks

This document positions our framework against the publicly known
methodologies of the four primary incumbents in DeFi risk analysis for
Morpho-style isolated lending markets: LlamaRisk, Block Analitica,
Gauntlet, and ChaosLabs. We compare on three dimensions: methodology,
findings, and operational fit. The goal is not to claim superiority
but to establish where our framework sits in the existing landscape
and what it adds.

We rely exclusively on public publications (firm blogs, dashboards,
Discourse posts, conference talks). Internal methodologies of these
firms are not public and may differ from what is described here.

---

## 1. Methodology comparison

| Dimension | Our framework | LlamaRisk | Block Analitica | Gauntlet | ChaosLabs |
|---|---|---|---|---|---|
| Regulatory anchor | BCBS 238 (LCR) explicit | Implicit | Implicit | Not stated | Not stated |
| Stress model | Window-worst re-mark + empirical outflow alpha; class-aware extreme (two legs); multi-day option | Single scenario | Single scenario | Agent-based simulation | Agent-based simulation |
| Position sampling | Actual onchain book (Morpho API, coverage-checked) | Empirical reconstruction | Empirical reconstruction | Empirical reconstruction | Empirical reconstruction |
| Backtest validation | 3 historical events, 2/3 PASS | Not published | Not published | Not published | Not published |
| Reproducibility | Open source, 146 tests passing | Internal only | Internal only | Internal only | Internal only |
| Severity tiers | Red / yellow / green on the survival frontier alpha* | Continuous score | Categorical (low/med/high) | Continuous risk-adjusted | Continuous risk-adjusted |
| Calibration source | Historical events (KelpDAO 2026, USDC 2023, stETH 2022) | Multi-source proprietary | Multi-source proprietary | Agent simulations | Agent simulations |

Three observations from this table:

**Observation 1.** No incumbent publishes an explicit regulatory anchor.
LlamaRisk and Block Analitica use Basel-adjacent concepts (liquidity
coverage, asset-class scoring) but do not formally identify their
ratios with BCBS 238 or BCBS 295. This makes their reports informative
for practitioners but not directly comparable across protocols. Our
explicit BCBS 238 alignment is a contribution to comparability rather
than a claim of correctness.

**Observation 2.** Agent-based simulation (Gauntlet, ChaosLabs) is more
sophisticated than our contract-faithful Monte Carlo on the dynamics it can
capture, in particular maximal-extractable-value, liquidator
competition, and gas-fee feedback. We acknowledge this in our
limitations section. Our framework is intentionally simpler to be
reproducible end-to-end on a developer laptop in under five minutes.
This is a deliberate scope choice, not a methodological gap.

**Observation 3.** Empirical position data is now standard for all
incumbents, and since v1.1 it is the only path in this framework as
well: the v1.0 parametric fallback is retired, and every evaluation
runs on the actual position book served by the Morpho API, with
per-market borrow-share coverage checked against onchain state.

---

## 2. Findings comparison

We compare our findings against the most recent public publications
from LlamaRisk and Block Analitica that cover any of our 26 analysed
markets. We restrict to publications dated within 90 days of our
analysis window.

### 2.1 Pendle principal tokens (PT-apyUSD, PT-apxUSD, PT-reUSD)

**Our finding (v1.1).** The roster's three Pendle principal-token
markets are past maturity at the current snapshot: their exit is par
redemption, not secondary depth, and the engine excludes them by
nature with that stated reason. The framework carries a dedicated
Pendle-router depth path for live principal tokens, and the v1.0
draft had flagged the then-live PT market red, consistent with the
incumbents' caution below.

**LlamaRisk position.** LlamaRisk has published flagging notes on PT
collateral types since their introduction on Morpho, identifying
liquidity gap-risk during volatility regimes as the dominant concern
(LlamaRisk Forum, *Pendle PT collateral risk assessment*, accessible at
forum.llamarisk.com).

**Block Analitica position.** Block Analitica curates several
MetaMorpho vaults that maintain modest exposure to PT-collateralised
markets. Their public dashboards (linked from
metamorpho.org/vaults) show explicit allocation caps on PT markets
typically below 10% of vault TVL.

**Convergence.** Three independent sources (LlamaRisk public, Block
Analitica curation behaviour, our framework) converge on the same
qualitative finding: PT tokens require explicit risk management. Our
contribution is the maturity-regime treatment: redemption-at-par
exclusion for matured principal tokens, and a measured router-depth
path for live ones.

### 2.2 Mainstream BTC/ETH-collateral markets (cbBTC, WBTC, wstETH)

**Our finding (v1.1).** These markets sit in the yellow band of the
survival frontier (10-30% of supply absorbable in 24 hours) with
negligible latent insolvency; exact per-market figures are in the
generated table of REPORT section 4.4.

**LlamaRisk position.** Mainstream wrapped BTC and liquid staking
markets are typically classified in their lowest risk tier in periodic
reports. LlamaRisk does not generally publish 99th-percentile bad
debt magnitudes.

**Block Analitica position.** Their MetaMorpho vaults aggregate
exposure heavily to these markets, treating them as the conservative
core of the Morpho deposit allocations.

**Convergence vs divergence.** Qualitative agreement on the core
robustness of these markets. Our addition is a quantified survival
frontier where incumbents report qualitative low risk: a continuous,
snapshot-stamped measure of how much of the book can exit in 24 hours,
consistent with the 'low-but-not-zero' regime that LlamaRisk and
Block Analitica qualitatively describe.

### 2.3 Liquid staking with high LLTV (wstETH/WETH 96.5%, weETH/WETH 94.5%)

**Our finding (v1.1).** These leverage-tier markets fail the extreme
test on the liquidity leg (stressed exit depth cannot absorb the
outflow) while latent insolvency stays contained; the failure mode is
liability-liquidity, not asset-solvency, which is the panorama's
central dichotomy.

**LlamaRisk position.** Recent forum notes flag the risk of high-LLTV
liquid staking markets specifically when the underlying staking yield
diverges from the implied yield in the borrow rate.

**Convergence.** Both sources identify high-LLTV LST markets as a
structural risk pattern. The driver in our analysis (thin stressed
exit depth against the outflow at high utilisation, with liquidation
margins compressed under a 25% drawdown) is consistent with the
LlamaRisk explanation (yield divergence triggers cascading
liquidations at compressed margin).

### 2.4 Synthetic stablecoins (sUSDe, sUSDS, wsrUSD)

**Our finding (v1.1).** On the survival frontier, synthetic-stable
markets spread across the red and yellow bands at target utilisation;
none clears the green threshold at the current snapshot. Two exotic
entries are excluded by nature (msY for an unsupported oracle
interface, permissioned wrappers for the absence of a public exit
venue), with the reason stated per market.

**LlamaRisk position.** sUSDe and sUSDS are typically classified as
medium risk in LlamaRisk taxonomies due to their depeg history (USDe
2024 minor depeg events) and complexity of the underlying yield
mechanism.

**Convergence (revised in v1.1).** The v1.0 draft classified these
markets more favourably than LlamaRisk; the v1.1 evaluation on the
actual book and measured depth moves them into the cautious bands,
closer to the LlamaRisk stance. The residual difference is horizon
framing: a 24-hour liability-liquidity view here, a multi-month
structural view there.

---

## 3. Operational fit comparison

| Use case | Best framework |
|---|---|
| Periodic regulatory-style market panorama (snapshot) | Our framework (open-source, reproducible) |
| Real-time alerting on parameter drift | Block Analitica (production dashboards) |
| Pre-launch parameter calibration | Gauntlet / ChaosLabs (agent simulation) |
| Regulatory comparability | Our framework (BCBS 238 anchor) |
| Investigative deep-dives on specific markets | LlamaRisk (qualitative depth) |
| End-to-end protocol risk monitoring | Combined: incumbents for live monitoring + our framework for periodic regulatory-style reports |

---

## 4. What our framework does that incumbents do not

**Three contributions specific to this work**:

1. **Explicit BCBS 238 mapping** with stated limitations. We document
   exactly which assumptions of the regulatory standard apply to DeFi
   and which require adaptation. No incumbent publishes this mapping.

2. **Reproducible backtest** against three historical stress events.
   We report 2/3 PASS and 1/3 FAIL (the FAIL is an out-of-scope
   multi-day repricing). No incumbent publishes a backtest framework
   that allows external verification.

3. **A survival-frontier verdict on the actual book.** The primary
   metric is the largest 24-hour outflow a market absorbs from
   measured, keeper-gated exit capacity, with an explicit split
   between realized bad debt and latent insolvency. The decomposition
   isolates liability-liquidity risk from asset-solvency risk, the
   dichotomy the panorama documents.

The trade-off is that we do not capture the dynamic effects (MEV,
liquidator competition, oracle feedback) that agent-based simulations
capture. For a complete risk assessment, our framework should be
combined with incumbent agent-based work, not replace it.

---

## 5. References for incumbent positions

- LlamaRisk Forum: forum.llamarisk.com
- Block Analitica: metamorpho.org/vaults (allocation dashboards)
- Gauntlet Methodology: docs.gauntlet.network
- ChaosLabs Methodology: chaoslabs.xyz/methodology

We treat all incumbent positions as paraphrased from public sources;
no quoted material is reproduced from these references.
