> **Document status.** This is the historical v0.3 design note and retains the theoretical foundations and calibration rationale used during development. The normative v1.1 public specification is [`REPORT.md`](./REPORT.md), read together with [`MODEL_CORRECTIONS.md`](./MODEL_CORRECTIONS.md) and the implementation. The forward-looking asset-class tables, Scenario A/B architecture, Top-five scope and Beta-scaled position model below are retained only to document the framework's evolution and are superseded for current results.

# Methodology: Liquidity Stress Testing Framework for Morpho Blue

> Version: 0.3 historical design note. Last updated: July 2026
> Status: retained methodological record; not the normative v1.1 result specification
> Companion: [`SCENARIOS.md`](./SCENARIOS.md). stress-scenario specifications;
> [`GLOSSARY.md`](./GLOSSARY.md). definitions of all specialised terms.
> Author: PA

---

## A note on terminology

This document defines every specialised term either at first use or in
[`GLOSSARY.md`](./GLOSSARY.md). Mathematical symbols are introduced
with their units. Abbreviations are spelled out on first use, with the
abbreviation in parentheses, and used as the abbreviation thereafter
within a single section.

---

## 1. Research question

### 1.1 Primary hypothesis (falsifiable)

We adopt the Popperian standard: a primary hypothesis is a claim
formulated such that observations could refute it.

Given the on-chain state of a Morpho Blue lending market $M$ at block
$t$, characterised by the tuple
$(S_t, B_t, \Lambda, \text{oracle}, \text{interest rate model}, \pi)$
where $S_t$ is total supply (loan-asset units), $B_t$ is total borrow
(loan-asset units), $\Lambda$ is the liquidation loan-to-value
threshold (a market parameter, $\in [0,1]$), and $\pi$ is the
slippage curve of the collateral on the relevant decentralised
exchange, there exists a stress scenario $\sigma$ such that, at
horizon $h$ blocks, the market enters one of two distress states:

- **Illiquid state**: incapacity to satisfy supplier withdrawal demand
  at block $t + h$, formally:
  $W_{\text{requested}}(t, t+h) > L(t+h)$
  where $W_{\text{requested}}$ is cumulative requested withdrawals and
  $L = S - B$ is the available liquidity.

- **Insolvent state**: realised bad debt $B_{\text{bad}}(t+h) > 0$,
  meaning that liquidations failed to fully cover defaulted positions
  due to collateral price gaps, oracle deviation, or liquidator
  decentralised-exchange slippage.

The probability of these states is bounded **empirically** from a
12-month rolling historical window, calibrated on observed stress
events (the KelpDAO collateral exploit of April 2026, the USDC depeg
of March 2023, and the staked-Ether discount episode of May 2022).

### 1.2 Secondary hypothesis (vault-curator angle; v1.0 analysis archived, see `docs/archive/metamorpho_v1.0.md`)

For a MetaMorpho vault $V$ with curator $c$ at block $t$, define the
**risk-discipline gap**:

$$\Delta(V, t) = \left\| X_{\text{observed}}(V, t) - X^\star(V, t) \right\|_2$$

where:
- $X_{\text{observed}}$ is the curator's actual allocation vector
  across approved Morpho Blue lending markets, indexed by market
  identifier;
- $X^\star$ is the theoretical allocation that minimises 30-day
  liquidity Value-at-Risk under the stress framework defined in this
  document;
- $\|\cdot\|_2$ denotes the Euclidean norm.

$\Delta$ is a proposed quantitative measure of curator risk discipline. In
the public materials reviewed for this project, incumbent risk reports focus
primarily on individual-market or vault risk and do not publish the same
curator counterfactual. This observation is scoped to the reviewed materials,
not a claim of exhaustive literature priority.

### 1.3 Why this matters

- **Academic gap**: Chiu, Ozdenoren, Yuan and Zhang (Bank for
  International Settlements Working Paper 1062, 2023) show that
  decentralised-finance lending pools are inherently fragile, but
  published work focuses on monolithic pools (Aave, Compound). Morpho
  Blue's *isolated-market design*, in which each market is an
  immutable tuple sharing no liquidity with others, has no comparable
  formal stress-testing framework.

- **Industry gap**: Risk reports from Gauntlet, Block Analitica and
  LlamaRisk transpose Basel concepts informally. We provide an
  **explicit Basel III mapping** with stated limitations.

- **Timing**: The KelpDAO event of April 2026 generated substantial bad debt
  on Aave and was followed by a material migration of capital toward Morpho.
  It provides a recent calibration anchor. Exact loss and flow estimates depend
  on the measurement perimeter and should be cited from the underlying event
  sources when used outside this methodological note.

---

## 2. Theoretical framework

### 2.1 Adaptation of the Liquidity Coverage Ratio

The Liquidity Coverage Ratio defined by the Basel Committee on Banking
Supervision (the *Basel Committee* hereafter) in document BCBS 238
(2013) is

$$\text{Liquidity Coverage Ratio} = \frac{\text{High Quality Liquid Assets}}{\text{Net cash outflows over 30 days}} \geq 100\%.$$

The **High Quality Liquid Assets** (the numerator, abbreviated *HQLA*
in this document for brevity from now on) are defined by the Basel
Committee in three tiers:

- **Level 1**: cash, central-bank reserves, and top-rated sovereign
  debt, haircut 0% (the haircut being the fraction of value assumed
  lost on monetisation under stress).
- **Level 2A**: highly liquid corporate or covered bonds, haircut
  15%.
- **Level 2B**: lower-rated corporate or equity, haircut 25 to 50%.

The **net cash outflows** (the denominator) are computed under a
stress scenario specified by the Basel Committee, with runoff factors
(percentages of liabilities expected to be withdrawn) ranging from
5% (insured retail deposits) to 100% (unsecured wholesale funding by
financial corporates).

We construct an on-chain analogue of the Liquidity Coverage Ratio for
a Morpho Blue lending market $M$ at block $t$, denoted
$\mathrm{LCR_{oc}}(M, t, \sigma, h)$, where the subscript "oc" stands
for "on-chain", and where $\sigma$ is the stress scenario and $h$ is
the horizon in blocks:

$$\mathrm{LCR_{oc}}(M, t, \sigma, h) = \frac{L_1(M, t) \,+\, L_{2A,\mathrm{net}}(M, t, \sigma)}{O_\sigma(M, t, h) - \min\left(I_\sigma(M, t, h), 0.75 \cdot O_\sigma\right)}$$

where:
- $L_1(M, t) = S_t - B_t$ is the on-chain analogue of HQLA Level 1
  (instant liquidity, no haircut);
- $L_{2A,\mathrm{net}}(M, t, \sigma)$ is the per-position liquidation
  recovery under stress (defined in §2.2 below);
- $O_\sigma(M, t, h) = \alpha \cdot S_t$ is the stress outflow, with
  $\alpha$ event-calibrated (defined in §2.4 below);
- $I_\sigma(M, t, h)$ is the inflow from forced repayments through
  liquidations during the stress window;
- The cap at 75% reproduces BCBS 238 Annex 4 §170, which limits the
  offset between secured-lending inflows and outflows.

The mapping from Basel definitions to Morpho Blue analogues is:

| Basel component | Basel definition | Morpho Blue analogue |
|---|---|---|
| HQLA Level 1 (haircut 0%) | Cash, central-bank reserves, top sovereign debt | Instant liquidity $L_1 = S - B$ |
| HQLA Level 2A (haircut 15%) | Highly liquid corporate or covered bonds | Per-position liquidation recovery, capped at debt and discounted by stress slippage (see §2.2) |
| HQLA Level 2B (haircut 25–50%) | Lower-rated corporate or equity | Collateral with limited decentralised-exchange liquidity (exotic liquid-restaking-tokens, real-world-asset tokens), with slippage drawn from the upper tail of the empirical distribution |
| Outflows: stable retail (5%) | Insured retail deposits | Approximated by the median of the drawdown-derived outflow proxy |
| Outflows: less-stable retail (10%) | Non-insured retail deposits | Approximated by the 90th percentile of the drawdown-derived outflow proxy |
| Outflows: wholesale unsecured (40–100%) | Non-financial or financial-corporate funding | Whale concentration: simultaneous withdrawal by the top-five suppliers under stress |
| Inflows: secured lending (cap 75%) | Repayments and collateral inflows | Forced repayments from liquidations during the stress window |

### 2.2 Per-position liquidation recovery (the on-chain Level 2A)

A literal application of a Basel Level 2A haircut to total collateral
notional value over-estimates recoverable liquidity. Collateral is pledged
and becomes monetisable only when a position is liquidatable and a keeper is
willing to execute the liquidation.

For a liquidatable position $i$, Morpho Blue determines the debt repaid and
the collateral seized under the protocol liquidation rules. The supplier
pool's realised recovery is the loan asset repaid by the liquidator, capped
by the position debt. Decentralised-exchange proceeds do **not** flow directly
to the supplier pool: they determine whether the keeper can profitably execute
the liquidation.

Let $q_i$ be the debt amount repaid by the liquidator. The realised recovery is

$$r_i = q_i, \qquad 0 \le q_i \le b_i.$$

Keeper executability is checked by comparing the value of seized collateral
after aggregate slippage with the repayment and liquidation incentive. If the
trade is not executable, the realised recovery is zero for that attempted
batch. The model therefore reports two separate solvency readings:

- **realised bad debt**, produced by the protocol-aligned liquidation engine;
- **latent insolvency**, the stressed debt not covered by collateral on oracle
  terms, computed independently of keeper behaviour.

The aggregate on-chain Level 2A component is

$$L_{2A,\mathrm{net}}(M,t,\sigma) = \sum_i r_i.$$

The liquidation incentive factor $\phi$ follows Morpho Blue's formula

$$\phi(\Lambda) = \min\left(1.15, \frac{1}{0.3 \cdot \Lambda + 0.7}\right),$$

with the bonus capped at 15%. The implementation details and corrections from
the superseded v0.3 recovery equation are catalogued in
`docs/MODEL_CORRECTIONS.md`.

### 2.3 Honest critique of the adaptation

The mapping in §2.1 is non-trivial; several choices are defensible
but not unique. We list the tensions explicitly:

1. **Time-unit mismatch**: the Basel Committee reasons in months;
  on-chain we measure in blocks (12 seconds on Ethereum). The Basel
  parameter $h = 30$ days is not natural; we expose $h$ as a free
  parameter and report results at three horizons: 24 hours, 7 days,
  30 days.

2. **No equivalent of "stable funding"**: in decentralised-finance
  lending, all suppliers are 100% callable by construction. The
  Basel concept of "operational deposits" has no on-chain analogue.
  We therefore expect that *all decentralised-finance lending pools
  have a structurally low Net Stable Funding Ratio* by Basel
  standards (see §2.5 below). The Liquidity Coverage Ratio is most
  informative *relative to itself* across markets and over time, not
  in absolute terms.

3. **Oracle as exogenous**: we treat oracle prices as exogenous
  inputs in the baseline. In reality, oracle behaviour
  (time-weighted-average-price smoothing, deviation thresholds,
  fallback logic) is endogenous to the stress scenario. This is a
  deliberate baseline simplification, modelled as a sensitivity
  analysis, not a structural feature.

### 2.4 Event-calibrated outflow fraction

The outflow fraction $\alpha$ in §2.1 is *not* a Basel-style
universal constant. It is derived from each market's own price-drawdown
distribution as a proxy for withdrawal velocity:

$$\alpha = \min\left(0.60, \max\left(0.05, 1.5 \cdot q_{0.99}(\mathrm{drawdowns}) + 0.30 \cdot \mathbf{1}\{q_{0.99}(\mathrm{drawdowns}) > 0.05\}\right)\right)$$

where:
- $q_{0.99}(\mathrm{drawdowns})$ is the 99th-percentile empirical
  quantile of 24-hour collateral price drawdowns over the past
  rolling year, expressed as a fraction;
- $\mathbf{1}\{\cdot\}$ is the indicator function.

The constant $1.5$ and the additive 30% (the *whale-concentration
term*) are anchored on observed withdrawal episodes, as discussed in [`REPORT.md`](./REPORT.md) §2.1.

### 2.5 The Net Stable Funding Ratio: a more discriminating angle

The Net Stable Funding Ratio defined in BCBS 295 (2014) is

$$\text{Net Stable Funding Ratio} = \frac{\text{Available Stable Funding}}{\text{Required Stable Funding}} \geq 100\%.$$

For decentralised-finance lending, a brute-force application yields:

- **Available Stable Funding weight**: suppliers are instantly
  callable, so the Available Stable Funding factor is approximately
  0%;
- **Required Stable Funding weight**: borrows have no contractual
  maturity (perpetual), so the Required Stable Funding factor is
  approximately 100%.

The Net Stable Funding Ratio is therefore approximately 0 for any
decentralised-finance lending pool. This is a **structural insight
rarely articulated in decentralised-finance risk literature**, because
crypto-native analysts typically do not work in the Basel framework.

The interesting analysis is the **conditional Net Stable Funding
Ratio**: how much funding is *empirically* stable, given oracle
health, prevailing yield differential versus alternatives, and
supplier concentration? This reduces to estimating a
*withdrawal-survival function* $S(t \mid \text{features})$, which could be modelled with Kaplan-Meier-style empirical survival curves on
historical supplier behaviour. This remains a proposed extension beyond the
current v1.1 publication rather than a validated output of the present engine.

---

## 3. Scope

### 3.1 Markets

Historical v0.3 design scope: the five largest Morpho Blue lending markets by
Total Value Locked on Ethereum mainnet at the start of data acquisition. The
v1.1 publication supersedes this scope: it monitors 26 markets and reports
results for the 24 markets that passed the published data-quality gates. The
current selector is implemented in
[`scripts/select_markets.py`](../scripts/select_markets.py).

**Historical candidate set (not the current v1.1 market universe)**:
- wstETH/USDC (collateral: wrapped staked Ether; loan asset: USDC)
- wstETH/WETH (collateral: wrapped staked Ether; loan asset: wrapped Ether)
- WBTC/USDC (collateral: wrapped Bitcoin; loan asset: USDC)
- cbBTC/USDC (collateral: Coinbase-wrapped Bitcoin; loan asset: USDC)
- sUSDe/USDC (collateral: staked Ethena USD; loan asset: USDC)

Historical selection criteria, in order: (i) Total Value Locked greater
than 100 million U.S. dollars, (ii) market age greater than 6 months, and
(iii) at least one stress event observable in the historical window. The
current v1.1 selector and data-quality gates are documented in `REPORT.md` and
implemented in `scripts/select_markets.py`.

### 3.2 Historical window

Twelve rolling months: May 2025 through May 2026. This window contains:

- The KelpDAO collateral exploit and ensuing migration of Total Value
  Locked (April 2026), used as the **primary calibration anchor**;
- A series of oracle deviations and minor depegs (continuous, low
  intensity);
- A prospective third-quarter 2025 macro-stress placeholder was included in
  the v0.3 design. It was not used as a calibration anchor in the v1.1 public
  results and is retained here only as part of the historical specification.

### 3.3 Stress horizons

Three values of $h$, reported in parallel:

- **24 hours**, equivalent of an intraday liquidity squeeze;
- **7 days**, short-horizon stress;
- **30 days**, Basel-equivalent horizon.

### 3.4 Historical stress-scenario design (four plus one)

> **Superseded for current results.** This section records the v0.3 scenario
> architecture. The current v1.1 evaluation is specified in `REPORT.md` and
> `MODEL_CORRECTIONS.md`.

Five scenarios were specified in [`SCENARIOS.md`](./SCENARIOS.md).
Summary:

| Identifier | Scenario | Description | Severity calibration |
|---|---|---|---|
| **S1** | Withdrawal run | Suppliers withdraw fraction $\alpha$ of total supply over duration $T$ | $\alpha$ at the 99th percentile of the drawdown-derived outflow proxy, $T \in \{1\text{h}, 24\text{h}, 7\text{d}\}$ |
| **S2** | Utilisation spike | Sudden borrow demand pushes utilisation toward 1 | Spike calibrated on the top-three historical events |
| **S3** | Oracle deviation | Collateral price drops by $\Delta$ in $\Delta t$; oracle reports lagged price | $\Delta$ at the 99th-percentile of historical drawdowns over $\Delta t$ |
| **S4** | Liquidation cascade | Combination: oracle drop with liquidations and decentralised-exchange slippage feedback | All three at the 95th-percentile jointly |
| **S5** | KelpDAO replay | Backtest of the April 2026 event applied to current Morpho markets ex-post | Empirical, no parameter |

### 3.5 Output metrics

For each (market, scenario, horizon) tuple:

- $\mathrm{LCR_{oc}}$, the primary metric, reported as
  a time series and worst-case;
- *Time-to-illiquid*: first block at which available liquidity is
  exhausted under the scenario;
- *Expected bad debt*: sum of unrecovered debt at end of horizon;
- *Slippage-adjusted shortfall*: gap between oracle-priced collateral
  and keeper-executable protocol repayment;
- *Withdrawal survival curve*: empirical $S(t \mid \sigma)$ for the
  secondary hypothesis.

---

## 4. Historical v0.3 limitations

The current v1.1 limitations are stated in `REPORT.md`. The items below are
retained to document the baseline design and should not be read as an
exhaustive list for the current engine.

1. **Endogeneity ignored at baseline**: prices, withdrawals, and
  liquidations are treated as separable processes. In reality,
  large liquidations move decentralised-exchange prices, which
  trigger more liquidations (a feedback loop). Capponi and Jia
  (2021) and follow-up work formalise this. Modelling it requires
  agent-based simulation or a fixed-point solver, out of scope at
  the baseline; flagged for a future version.

2. **Oracle as exogenous input**: time-weighted-average-price
  behaviour, fallback paths, and oracle outages are not endogenously
  modelled. Sensitivity analysis only.

3. **Maximal extractable value and liquidator competition**:
  liquidations are assumed perfect (no liquidator stuck in mempool,
  no priority-gas-auction failure). This biases bad-debt estimates
  downward at the baseline.

4. **Cross-market contagion**: by Morpho Blue design, lending markets
  are isolated, so there is no cross-market contagion at the
  protocol layer. *However*, MetaMorpho vaults link markets
  economically through curator allocation. Vault-level analysis (the
  secondary hypothesis) introduces this dimension.

5. **Calibration on a short window**: 12 months of data on a
  fast-evolving protocol means small-sample bias. Confidence
  intervals are reported but should be taken as indicative.

6. **Monte Carlo as retained extension**: scenarios are designed in
  dual mode, point (deterministic shocks at empirical quantiles)
  and Monte Carlo (sampled from empirical distributions, with $N$
  paths and confidence intervals). Monte Carlo is *not* deferred
  future work: it is part of the baseline specification (see
  [`SCENARIOS.md`](./SCENARIOS.md) §5). The honest caveat is
  statistical: a 12-month sample produces wide confidence intervals
  on tail quantiles. The 99th-percentile is estimated from
  approximately three disjoint or 88 overlapping observations.
  Block bootstrap and Pareto-tail sensitivity tests are used to
  bound this uncertainty, but tail estimation on short
  decentralised-finance history remains the dominant source of
  model risk.

7. **Solidity behaviour not simulated end-to-end**: we model the
  economic state, not gas or mempool dynamics. A full Foundry
  fork-test would close this gap.

8. **Smart-contract risk excluded**: the framework assumes Morpho
  Blue contracts execute correctly. Contract-level risk (bugs,
  governance attacks) is out of scope.

---

## 5. References

See [`references.md`](./references.md) for the full bibliography. Core
anchors:

- **Basel framework**: BCBS 238 (Liquidity Coverage Ratio, 2013); BCBS
  295 (Net Stable Funding Ratio, 2014).
- **Decentralised-finance lending theory**: Gudgeon, Werner, Perez and
  Knottenbelt (2020); Capponi and Jia (2021, 2023); Chiu, Ozdenoren,
  Yuan and Zhang (Bank for International Settlements Working Paper
  1062, 2023).
- **Protocol specification**: Morpho Labs, *Morpho Blue Whitepaper*
  and *Morpho Blue Yellow Paper*.
- **Industry benchmarks**: Steakhouse Financial public Maker
  analyses; Block Analitica risk reports; LlamaRisk Aave and Curve
  reports.

---

## 6. Document version control

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-05-04 | Initial draft (Phase 0) |
| 0.2 | 2026-05-04 | §4.6, Monte Carlo retained as baseline extension; companion `SCENARIOS.md` published |
| 0.3 | 2026-05-05 | All abbreviations spelled out at first use; per-position liquidation recovery (§2.2) introduced; companion `GLOSSARY.md` published |
