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
| Stress model | Decoupled scenarios A/B + extreme + multi-day | Single scenario | Single scenario | Agent-based simulation | Agent-based simulation |
| Position sampling | Beta-scaled OR empirical reconstruction | Empirical reconstruction | Empirical reconstruction | Empirical reconstruction | Empirical reconstruction |
| Backtest validation | 3 historical events, 2/3 PASS | Not published | Not published | Not published | Not published |
| Reproducibility | Open source, 145 tests passing | Internal only | Internal only | Internal only | Internal only |
| Severity tiers | Red / yellow / green-watch / green-strong | Continuous score | Categorical (low/med/high) | Continuous risk-adjusted | Continuous risk-adjusted |
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
sophisticated than our parametric Monte Carlo on the dynamics it can
capture, in particular maximal-extractable-value, liquidator
competition, and gas-fee feedback. We acknowledge this in our
limitations section. Our framework is intentionally simpler to be
reproducible end-to-end on a developer laptop in under five minutes.
This is a deliberate scope choice, not a methodological gap.

**Observation 3.** Empirical position reconstruction is now standard
for all incumbents. Our parametric Beta is a fallback; the
`scripts/enrich_positions.py` deliverable adds empirical reconstruction
from on-chain Borrow/Repay events. The remaining gap is collateral-event
processing (SupplyCollateral/WithdrawCollateral), which is a Phase 7
extension.

---

## 2. Findings comparison

We compare our findings against the most recent public publications
from LlamaRisk and Block Analitica that cover any of our 26 analysed
markets. We restrict to publications dated within 90 days of our
analysis window.

### 2.1 Pendle principal tokens (PT-apyUSD, PT-apxUSD, PT-reUSD)

**Our finding.** PT-apyUSD-18JUN2026/USDC is flagged red under nominal
stress with 99th-percentile bad debt at 5.7% TVL. All three Pendle PT
markets fail the extreme stress test.

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
contribution is the quantitative magnitude (5.7% TVL bad debt at p99)
under a stated stress scenario.

### 2.2 Mainstream BTC/ETH-collateral markets (cbBTC, WBTC, wstETH)

**Our finding.** Yellow tier with material absolute exposure: $13.3M
of cumulative 99th-percentile bad debt across the four markets,
representing 1.4-2.4% of each market's TVL.

**LlamaRisk position.** Mainstream wrapped BTC and liquid staking
markets are typically classified in their lowest risk tier in periodic
reports. LlamaRisk does not generally publish 99th-percentile bad
debt magnitudes.

**Block Analitica position.** Their MetaMorpho vaults aggregate
exposure heavily to these markets, treating them as the conservative
core of the Morpho deposit allocations.

**Convergence vs divergence.** Qualitative agreement on the core
robustness of these markets. The divergence is that we report a
non-zero bad debt magnitude where incumbents report low risk
qualitatively. This is a function of the precision of the metric, not
a disagreement on the underlying risk: 1.4-2.4% of TVL is consistent
with the 'low-but-not-zero' regime that LlamaRisk and Block Analitica
qualitatively describe.

### 2.3 Liquid staking with high LLTV (wstETH/WETH 96.5%, weETH/WETH 94.5%)

**Our finding.** These leverage-tier markets fail the extreme stress
test (10.52% and 10.29% bad debt of TVL respectively).

**LlamaRisk position.** Recent forum notes flag the risk of high-LLTV
liquid staking markets specifically when the underlying staking yield
diverges from the implied yield in the borrow rate.

**Convergence.** Both sources identify high-LLTV LST markets as a
structural risk pattern. The driver in our analysis (compressed margin
between average LTV and LLTV under a 25% drawdown) is consistent with
the LlamaRisk explanation (yield divergence triggers cascading
liquidations at compressed margin).

### 2.4 Synthetic stablecoins (sUSDe, sUSDS, wsrUSD)

**Our finding.** Mostly green-strong under nominal; sUSDe/PYUSD is
green-watch. Two exotic synthetic stablecoins (msY, sUSDat) fail
extreme stress, reported as known limitations due to low cardinality
of positions.

**LlamaRisk position.** sUSDe and sUSDS are typically classified as
medium risk in LlamaRisk taxonomies due to their depeg history (USDe
2024 minor depeg events) and complexity of the underlying yield
mechanism.

**Divergence.** We classify these markets more favourably than
LlamaRisk would, reflecting a focus on 24h LCR stress rather than
multi-month structural risk. Under our multi-day NSFR-style horizon
(`--horizon-days 7`), the same markets shift toward green-watch or
yellow, closer to the LlamaRisk classification.

---

## 3. Operational fit comparison

| Use case | Best framework |
|---|---|
| Vault curator risk discipline check (snapshot) | Our framework (open-source, reproducible) |
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

3. **Decoupled scenario architecture** for price stress and
   liquidity stress. The decomposition isolates the contribution of
   each stress component, addressing a methodological gap where
   cumulative-stress single scenarios over-estimate aggregate risk.

The trade-off is that we do not capture the dynamic effects (MEV,
liquidator competition, oracle feedback) that agent-based simulations
capture. For a comprehensive risk assessment, our framework should be
combined with incumbent agent-based work, not replace it.

---

## 5. References for incumbent positions

- LlamaRisk Forum: forum.llamarisk.com
- Block Analitica: metamorpho.org/vaults (allocation dashboards)
- Gauntlet Methodology: docs.gauntlet.network
- ChaosLabs Methodology: chaoslabs.xyz/methodology

We treat all incumbent positions as paraphrased from public sources;
no quoted material is reproduced from these references.
