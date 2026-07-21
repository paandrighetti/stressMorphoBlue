# A Liquidity Stress Framework for Morpho Blue, Adapted from Basel III

> **Summary**. We build a liquidity stress framework for Morpho Blue
> isolated lending markets, adapting the Liquidity Coverage Ratio
> defined by the Basel Committee on Banking Supervision in BCBS 238
> (2013). The framework is calibrated against three historical stress
> events (the KelpDAO exploit of April 2026, the USDC depeg of March
> 2023, and the staked-Ether discount episode of May 2022). Two of
> three events are correctly flagged ahead of the event by our
> pre-event detection criteria; the third failure is informative: the
> staked-Ether episode was a multi-day slow-rolling repricing rather
> than a 24-hour liquidity stress, and the framework correctly does
> not classify it as the latter.
>
> Applied forward (v1.1 engine) to the most material Morpho Blue
> isolated markets on Ethereum mainnet, on the **actual onchain
> position book** and on **measured exit depth**, the framework's
> primary metric is the **survival frontier**: the largest 24-hour
> outflow fraction a market absorbs from instantaneous liquidity plus
> stress-liquidatable recoveries under keeper executability. The
> headline finding is a dichotomy: the extreme scenario fails on the
> **liquidity leg** across the overwhelming majority of evaluated
> markets and supply, and on the **solvency leg** nowhere; latent
> insolvency stays negligible even under a 25% shock. At target
> utilisation, 24-hour risk on Morpho Blue is a liability-liquidity
> question, not an asset-solvency one, and survival in practice
> depends on rate-driven replenishment, which this version
> deliberately does not model. Exact figures, tiers and the snapshot
> stamp are generated into section 4.4 from the evaluation output and
> are never hand-transcribed.
>
> Curator-level analysis of MetaMorpho vault allocations is deferred
> to a follow-up publication; the superseded v1.0 draft is retained
> for historical reference in `docs/archive/metamorpho_v1.0.md`.
>
> The full source code, test suite, and reproducible event fixtures
> are open-source.

---

## A note on terminology

Every specialised term used in this document is defined either at first
use or in [`GLOSSARY.md`](./GLOSSARY.md). Mathematical symbols are
introduced explicitly with their units. Abbreviations are spelled out
on first use, with the abbreviation in parentheses, then used as the
abbreviation in subsequent references.

---

## 1. Motivation

Decentralised-finance lending pools have been shown to exhibit
inherent fragility under stress (Chiu, Ozdenoren, Yuan & Zhang, *On
the inherent fragility of decentralised-finance lending*, Bank for
International Settlements Working Paper 1062, 2023). Yet most public
risk reports for these pools transpose institutional concepts (such
as those defined by the Basel Committee on Banking Supervision,
abbreviated below as the *Basel Committee*) informally, without
explicit pass-or-fail criteria, and without a reproducible backtest
against historical events.

This work formalises the transposition. We build:

- An on-chain analogue of the Liquidity Coverage Ratio (the regulatory
  ratio defined in BCBS 238, 2013, which requires regulated banks to
  hold sufficient liquid assets to cover stressed outflows over 30
  days; see §2.1 below);
- A Monte Carlo simulation framework over an empirical distribution of
  collateral price drawdowns;
- A falsifiable validation procedure with three pre-specified
  pass-or-fail criteria.

The choice of Morpho Blue as the target protocol is motivated by:

- **Architectural simplicity**: Morpho Blue is a non-custodial lending
  protocol implemented in approximately 650 lines of Solidity, with
  isolated lending markets and immutable parameters. This produces a
  small surface area and a well-defined mathematical state vector for
  each market.
- **Industry positioning in 2026**: following the KelpDAO collateral
  exploit of April 2026, approximately 8 billion U.S. dollars of Total
  Value Locked has migrated from Aave to Morpho (per public on-chain
  data observed at the time of writing). Risk methodology adapted to
  Morpho's isolated-market design is in active demand among the
  protocol's MetaMorpho vault curators, including Steakhouse
  Financial, Block Analitica, and B.Protocol.

This work is methodological. The contribution is a falsifiable,
reproducible adaptation of regulatory liquidity standards to one
particular decentralised-finance protocol; it is neither a
production-grade risk-monitoring system nor a security audit.

---

## 2. The framework

### 2.1 Adaptation of the Liquidity Coverage Ratio

> Formulas in this section state the **v1.1 engine semantics**
> (single-counted recoveries, oracle-terms seizure, exhaustion-based bad
> debt, keeper executability). Historical v1.0 divergences are catalogued
> in [docs/MODEL_CORRECTIONS.md](MODEL_CORRECTIONS.md).

The Liquidity Coverage Ratio defined by the Basel Committee in BCBS
238 (2013) is

$$\text{Liquidity Coverage Ratio} = \frac{\text{High Quality Liquid Assets}}{\text{Net cash outflows over 30 days}} \geq 100\%.$$

We construct an **on-chain Liquidity Coverage Ratio** for a Morpho Blue
lending market. The numerator (High Quality Liquid Assets, a Basel
term referring to assets readily monetisable under stress with little
loss in value) is decomposed into two layers in the original Basel
text:

- *Level 1*: cash and equivalents, with a haircut of 0%;
- *Level 2A*: highly liquid bonds, with a haircut of 15%.

For a Morpho Blue lending market, our adaptation is as follows. Let:

- $S$ denote the total supply of the loan asset (denoted
  `total_supply_assets` on-chain), in units of the loan asset;
- $B$ denote the total borrow of the loan asset (denoted
  `total_borrow_assets` on-chain), in units of the loan asset;
- $L = S - B$ denote the instantaneous available liquidity, in units
  of the loan asset;
- $\Lambda$ denote the liquidation loan-to-value threshold (the
  market's parameter, fixed at market creation), a number in $[0, 1]$;
- For each borrower $i$: $b_i$ the borrower's debt (in loan-asset
  units), $c_i$ the borrower's collateral (in collateral-asset units);
- $P$ denote the oracle-reported price of one collateral unit in
  loan-asset units;
- $\pi(V) = a \cdot V^b$ denote the slippage of a sale of $V$
  collateral-asset units on a decentralised exchange, expressed as a
  fraction of the oracle price; the parameters $a > 0$ and $b \in (0,1)$
  are fitted from data per the Almgren, Chriss model (see §2.4).

The **on-chain Level 1 component** is the available liquidity:
$L_1 = L$.

The **on-chain Level 2A component** corresponds to the loan-asset
value the protocol can recover via liquidation under stress. The
liquidator seizes collateral up to a *liquidation incentive factor*
$\phi(\Lambda)$ above the debt amount (Morpho Blue's formula:
$\phi(\Lambda) = \min(1.15, 1/(0.3\Lambda + 0.7))$, capping the bonus
at 15%) and sells it on the decentralised exchange at the realised
price $P \cdot (1 - \pi(\cdot))$. The recovery for the supplier pool
from position $i$ is

$$r_i = \min\left(c_i \cdot P \cdot (1 - \pi(c_i)), b_i \cdot \phi(\Lambda)\right) - \mathrm{BD}_i$$

where the cap at $b_i \cdot \phi(\Lambda)$ reflects that the
protocol does not benefit from over-collateralisation (any surplus
returns to the borrower) and where the **bad debt** for position $i$
is

$$\mathrm{BD}_i = \max\left(0, b_i - c_i \cdot P \cdot (1 - \pi(c_i))\right),$$

i.e., the unrecoverable shortfall when realised proceeds fall below
the position's debt. The aggregate Level 2A is then
$L_{2A,\mathrm{net}} = \sum_i r_i$.

This formulation **differs from a literal Basel haircut transposition**
on a critical point: the Basel haircut applies to a notional asset
value, while our Level 2A is bounded above by the per-position debt.
This avoids the over-counting of pledged collateral that we observed
in earlier versions of this work (see §3 of [`SCENARIOS.md`](./SCENARIOS.md)
for the full discussion).

The **on-chain numerator** is then
$\mathrm{HQLA_{oc}} = L_1 + L_{2A,\mathrm{net}}$.

The **on-chain denominator** (net cash outflows under stress) is
parameterised by an **outflow fraction** $\alpha$, the fraction of
total supply withdrawn during the 24-hour stress window:

$$\mathrm{Outflows_{oc}}(\alpha) = \alpha \cdot S - \min\left(L_{2A,\mathrm{net}}, 0.75 \cdot \alpha S\right).$$

The cap at 75% of outflows reproduces BCBS 238 Annex 4 §170, which
limits the offset between secured-lending inflows and outflows.

The **outflow fraction $\alpha$ is event-calibrated** from the
empirical distribution of 24-hour drawdowns of the collateral price.
We use

$$\alpha = \min\left(0.60, \max\left(0.05, 1.5 \cdot q_{0.99}(\mathrm{drawdowns}) + 0.30 \cdot \mathbf{1}\{q_{0.99} > 0.05\}\right)\right)$$

where $q_{0.99}(\mathrm{drawdowns})$ is the 99th-percentile empirical
quantile of drawdowns, and $\mathbf{1}\{\cdot\}$ the indicator
function. The constant $1.5$ and the additive term $0.30$ use
collateral-price drawdowns as a provisional proxy for outflows, with
coefficients anchored on observed withdrawal episodes:

- During the KelpDAO event of April 2026, the Aave Total Value Locked
  fell by approximately 17% in 48 hours, peaking at approximately 10%
  in 24 hours, implying a withdrawal multiplier in the range
  $[1.4, 1.7]$ relative to the contemporaneous price drawdown.
- During the USDC depeg of March 2023, the Aave USDC market saw
  approximately 25% withdrawals on day one, consistent with a
  multiplier of $1.5$ applied to a drawdown of $\approx 12\%$, plus
  a whale-concentration term capturing rapid exit by the largest
  suppliers.

The whale-concentration term (the additive $0.30 \cdot \mathbf{1}\{q_{0.99} > 0.05\}$)
reflects the empirical observation that the top five suppliers in
mid-size decentralised-finance lending markets tend to exit at the
first sign of stress, contributing a near-instantaneous 30% withdrawal
of total supply.

### 2.2 Three criteria (v1.1)

Each market is evaluated on three criteria capturing distinct risk
channels:

| Criterion | Definition | Verdict role |
|---|---|---|
| Survival frontier $\alpha^*$ | largest 24-hour outflow fraction absorbed from instantaneous liquidity plus stress-liquidatable recoveries under keeper executability, with the oracle re-marked at the window-worst print | primary; carries the tiers (section 4.3) |
| Time-to-illiquid | first hour at which instantaneous liquidity is exhausted at the window-calibrated outflow $\alpha$ | companion marker |
| Solvency, two readings | realized bad debt from the contract-faithful Monte Carlo (keeper-gated), and latent insolvency: debt not covered by collateral on stressed oracle terms, keeper-independent | companion; under keeper strikes, latent insolvency is the number to read |

The empirical outflow $\alpha$ of each market's own window is reported
as a stress marker, not a verdict: its calibration is discontinuous at
the 5% large-holder trigger, which is precisely why the survival
frontier, a continuous quantity, carries the tiers.

### 2.3 Why three criteria?

A market may sit at a comfortable survival frontier yet drain quickly
under concentrated whale exit (short time-to-illiquid). Conversely, a
market may be slow to drain yet carry material latent insolvency under
a price shock. The three criteria are designed to be *non-redundant*:
empirically (see §3.2 below) different events trigger different
criteria, and the combination is required for adequate coverage.

### 2.4 Slippage curve

For each collateral asset, we fit a power-law impact function
$\pi(V) = a \cdot V^b$ via ordinary least squares regression in
log-space. The exponent $b$ typically lies in $[0.50, 0.62]$,
consistent with the equity-microstructure literature (Almgren and
Chriss, *Optimal execution of portfolio transactions*, Journal of
Risk, 2000; Frazzini, Israel and Moskowitz, *Trading Costs*, working
paper, 2018). Confidence intervals on $b$ are reported alongside the
point estimate using the Wald approximation (Gaussian asymptotics on
the regression coefficient, valid for ordinary least squares with
homoskedastic errors).

---

## 3. Backtest validation

### 3.1 Events selected

We backtest the framework against three historical stress events,
selected to span distinct risk profiles.

| Event | Type | Day-zero (T-zero) | Counterfactual? |
|---|---|---|---|
| **KelpDAO collateral exploit** | Liquid-restaking-token collateral exploit, single-day cascade | 2026-04-19 23:59 UTC | No, Morpho Blue was active |
| **USDC depeg from Silicon Valley Bank collapse** | Stable-on-stable depeg | 2023-03-10 12:00 UTC | Yes, predates Morpho Blue |
| **Staked-Ether discount during the Terra/UST collapse** | Liquid-staking-token discount, multi-day slow-roll | 2022-05-11 09:00 UTC | Yes, predates Morpho Blue |

The day-zero (denoted T-zero) is the timestamp at which the framework
is evaluated, set at 24 hours before the realised stress event. For
events that predate Morpho Blue, we apply the framework on a
*counterfactual* Morpho Blue market with parameters typical of current
practice (liquidation loan-to-value threshold, interest rate model,
oracle), seeded with the actual price path of the event.

### 3.2 Results

| Event | Liquidity Coverage Ratio | $\alpha$ | Time-to-illiquid | Probability bad debt > 0 | Severity | Verdict |
|---|---|---|---|---|---|---|
| KelpDAO 2026 | 8.30 (green) | 60% | < 6h (red) | high (red) | **red** | **PASS** |
| USDC depeg 2023 | 8.30 (green) | 48% | 6.6h (red) | 0% (green) | **red** | **PASS** |
| Staked-Ether 2022 | 80.0 (green) | 5% (floor) | infinite (green) | 0% (green) | **green** | **FAIL** |

**KelpDAO and the USDC depeg are flagged ahead of the event** through
the time-to-illiquid criterion at the event-calibrated $\alpha$. The
bad-debt-probability criterion fires only on KelpDAO. This is
informative: the USDC oracle was *sticky* during the depeg (the
Chainlink USDC-to-U.S.-dollar feed remained at $1.00$ for hours, while
the secondary market traded at approximately $0.88$), so on-chain
positions did not reach the liquidation threshold despite severe
market-price dislocations. The framework correctly captures that the
USDC event's risk channel was *liquidity drain* rather than *bad-debt
cascade*.

**The staked-Ether 2022 episode is not flagged.** We retain this
result rather than tune parameters to obtain three-of-three. The
staked-Ether discount unfolded slowly, from a ratio of 0.99 down to
0.94 staked-Ether-to-Ether over five days. Under our 24-hour rolling
window, the maximum observed drawdown falls below the 5% threshold
that triggers the whale-concentration term, and $\alpha$ collapses to
its floor of 5%. This is not a calibration failure: it is a **scope
limitation that we acknowledge openly**. Our framework adapts the
24-hour Liquidity Coverage Ratio of BCBS 238, not the
medium-horizon Net Stable Funding Ratio of BCBS 295 (2014). Capturing
the staked-Ether-style risk channel would require a complementary
adaptation of the Net Stable Funding Ratio. We flag this as future
work.

### 3.3 Aggregate verdict

**Two of three events are correctly flagged**, including the primary
anchor (KelpDAO). The single failure is a documented scope
limitation, not a parameter-tuning failure. We argue that this
honesty is more valuable than a three-of-three result obtained by
tuning thresholds to the test set: a risk methodology that pretends
to cover everything is a methodology that quietly misses real risks
in production.

---

## 4. Forward-looking analysis

### 4.1 Roster

We apply the framework to the **26 most material Morpho Blue isolated
markets on Ethereum mainnet**, ranked by Total Value Locked, with state
extracted from the on-chain data acquisition pipeline described in
[`docs/DATA.md`](./DATA.md). The roster is therefore not illustrative
but reflects the live composition of the protocol as observed during
the analysis window. Aggregate Total Value Locked across the roster is
approximately 1.7 billion U.S. dollars.

The roster spans five collateral asset classes:

- **Wrapped Bitcoin variants** (cbBTC, WBTC, LBTC), $635M total
- **Liquid staking tokens** (wstETH, weETH), $570M total
- **Synthetic stablecoins** (sUSDe, sUSDS, wsrUSD, syrupUSDC, AA_FalconXUSDC, sUSDat, stcUSD, msY, mF-ONE, stUSDS), $552M total
- **Pendle principal tokens** (PT-apyUSD, PT-apxUSD, PT-reUSD), $52M total
- **Yield-bearing wrappers** (sUSDe in different quote pairs), residual

Loan assets are dominated by USDC, USDT, PYUSD, and WETH.

### 4.2 Methodology: stressed-state evaluation (v1.1)

The v1.0 draft evaluated two decoupled scenarios (a price leg and a
liquidity leg) and reported the worst of the two; that machinery is
retired (section 4quater documents why). The v1.1 base evaluation:

- **re-marks each market at its window-worst oracle print** and derives
  the outflow $\alpha$ from the market's own empirical 24-hour drawdown
  distribution, with the documented discontinuity at the 5%
  large-holder trigger;
- **evaluates the actual onchain position book** served by the Morpho
  API, with per-market borrow-share coverage checked against onchain
  state, instead of any parametric position reconstruction;
- **prices exits on measured depth**: Uniswap V3 quoter curves for
  majors, keyless aggregator quotes rebased on the smallest executed
  size for yield-bearing and exotic collateral; per-snapshot venue
  coverage is whatever the quote cache holds at evaluation time;
- **runs contract-faithful liquidation** in the Monte Carlo:
  `Morpho.sol` exhaustion semantics, oracle-terms seizure, and keeper
  executability at the aggregate slippage of the eligible batch.

The class-aware drawdown floors of v1.0 survive only in the extreme
test of section 4bis (25% for volatile collateral; capped at three
times the window-worst move, floored at 5%, for redemption-arbitraged
pairs). The columns reported in section 4.4 are the survival frontier
$\alpha^*$, the empirical window $\alpha$ (marker), time-to-illiquid,
and the two solvency readings.

### 4.3 Severity tiers (v1.1)

Tiers are assigned on the survival frontier alone: `red` below 10%,
`yellow` below 30%, `green` at or above 30% of supply absorbable in 24
hours. The thresholds anchor to the framework's $\alpha$ calibration
band: 10% sits at the upper edge of observed non-event daily outflows,
and 30% covers a KelpDAO-class event with margin. Time-to-illiquid and
the solvency readings are reported as companions: they can escalate
attention within a tier but do not move it. The v1.0 composite
severity (built on $\Pr(\mathrm{LCR}<1)$, time-to-illiquid and
bad-debt bands, including the green-strong / green-watch subdivision
of `green`) is retired.

### 4.4 Risk panorama (engine v1.1, live positions)

Evaluated on the actual onchain position book (fetched via the Morpho API,
per-market borrow-share coverage verified against market state) and on
measured exit depth (Uniswap V3 quoter for majors; keyless CoW Protocol and
KyberSwap aggregator quotes, size-rebased, for yield-bearing and exotic
collateral). The primary discriminator is the survival frontier alpha\*, the
largest 24-hour outflow fraction a market absorbs from instantaneous
liquidity plus stress-liquidatable recoveries under keeper executability.

<!-- BEGIN GENERATED: report_results -->
### Results (engine v1.1)

**Snapshot**: 2026-07-16, state block 25,545,086. **24 of 26 monitored markets evaluated** (engine v1.1; exclusions documented below). Survival frontier alpha\*: median 10.7%, minimum 1.0%. Tiers on alpha\*: 16 red, 7 yellow, 1 green. Under the extreme scenario, **20 of 24 markets fail the liquidity leg while 0 fail the solvency leg**: at target utilisation, 24-hour risk on Morpho Blue is a liability-liquidity question, not an asset-solvency one.

#### Base 24h stress, sorted by survival frontier

| Market | Supply | U | alpha (window) | alpha\* | TTI | P(insolv) | Tier |
|---|---|---|---|---|---|---|---|
| AA_FalconXUSDC/USDC | $44.8M | 99% | 5% | **1.0%** | 4.9h | 0% | red |
| stcUSD/USDT | $1.4M | 93% | 5% | **7.1%** | inf | 0% | red |
| stUSDS/USDC | $16.7M | 91% | 5% | **9.0%** | inf | 0% | red |
| sUSDe/USDtb | $10.2M | 91% | 5% | **9.2%** | inf | 0% | red |
| mF-ONE/USDC | $16.3M | 90% | 5% | **9.8%** | inf | 0% | red |
| weETH/PYUSD | $52.1M | 90% | 41% | **9.8%** | 5.7h | 0% | red |
| wsrUSD/USDC | $17.8M | 90% | 5% | **9.8%** | inf | 0% | red |
| weETH/RLUSD | $67.3M | 90% | 41% | **9.8%** | 5.8h | 0% | red |
| wstETH/USDC | $30.7M | 90% | 40% | **9.9%** | 5.9h | 0% | red |
| cbBTC/USDC | $287.6M | 90% | 38% | **10.2%** | 6.4h | 0% | red |
| WBTC/USDC | $115.8M | 90% | 38% | **10.2%** | 6.4h | 0% | red |
| LBTC/PYUSD | $46.7M | 89% | 38% | **10.6%** | 6.7h | 0% | red |
| PT-apyUSD-18JUN2026/USDC | $3.2M | 89% | 46% | **10.8%** | 5.7h | 4% | red |
| syrupUSDC/RLUSD | $33.8M | 90% | 5% | **10.8%** | inf | 0% | yellow |
| wstETH/USDT | $172.7M | 89% | 40% | **10.9%** | 6.5h | 0% | red |
| sUSDe/PYUSD | $40.6M | 89% | 5% | **11.0%** | inf | 0% | yellow |
| wstETH/WETH | 11,554 WETH | 89% | 5% | **11.2%** | inf | 0% | yellow |
| wstETH/WETH | 48,995 WETH | 89% | 5% | **11.3%** | inf | 0% | yellow |
| weETH/WETH | 8,901 WETH | 89% | 5% | **11.4%** | inf | 0% | yellow |
| WBTC/USDT | $57.1M | 88% | 38% | **11.9%** | 7.5h | 0% | red |
| PT-apxUSD-18JUN2026/USDC | $212k | 86% | 46% | **13.7%** | 7.2h | 0% | red |
| cbBTC/PYUSD | $2.8M | 78% | 7% | **21.8%** | inf | 0% | yellow |
| sUSDat/AUSD | $8.9M | 75% | 41% | **24.8%** | 14.5h | 0% | yellow |
| PT-reUSD-25JUN2026/USDC | $640k | 59% | 5% | **41.1%** | inf | 0% | green |

alpha\* = stressed liquid stock / supply: the largest 24h outflow fraction the market absorbs (oracle at the window-worst price, recoveries from stress-liquidatable positions included, keeper executability enforced). Tier thresholds anchor to the framework's documented alpha calibration band: red < 10%, yellow < 30%, green >= 30%.

#### Extreme scenario (class-aware drawdown, 35% outflows)

| Market | dd applied | LSR (alpha=35%) | Latent insolvency | Illiquidity leg | Solvency leg |
|---|---|---|---|---|---|
| AA_FalconXUSDC/USDC | 5% | 0.03 | 0.00% | FAIL | pass |
| stcUSD/USDT | 5% | 2.86 | 0.00% | pass | pass |
| stUSDS/USDC | 5% | 1.35 | 0.00% | pass | pass |
| sUSDe/USDtb | 5% | 0.66 | 0.00% | FAIL | pass |
| mF-ONE/USDC | 5% | 0.28 | 0.00% | FAIL | pass |
| weETH/PYUSD | 25% | 0.28 | 0.02% | FAIL | pass |
| wsrUSD/USDC | 5% | 0.28 | 0.01% | FAIL | pass |
| weETH/RLUSD | 25% | 0.28 | 0.11% | FAIL | pass |
| wstETH/USDC | 25% | 0.28 | 0.00% | FAIL | pass |
| cbBTC/USDC | 25% | 0.29 | 0.02% | FAIL | pass |
| WBTC/USDC | 25% | 0.29 | 0.14% | FAIL | pass |
| LBTC/PYUSD | 25% | 0.32 | 0.00% | FAIL | pass |
| PT-apyUSD-18JUN2026/USDC | 25% | 0.31 | 0.25% | FAIL | pass |
| syrupUSDC/RLUSD | 5% | 0.84 | 0.00% | FAIL | pass |
| wstETH/USDT | 25% | 0.31 | 0.00% | FAIL | pass |
| sUSDe/PYUSD | 5% | 2.52 | 0.00% | pass | pass |
| wstETH/WETH | 5% | 0.32 | 0.01% | FAIL | pass |
| wstETH/WETH | 5% | 0.32 | 0.39% | FAIL | pass |
| weETH/WETH | 5% | 0.33 | 0.01% | FAIL | pass |
| WBTC/USDT | 25% | 0.34 | 0.69% | FAIL | pass |
| PT-apxUSD-18JUN2026/USDC | 25% | 0.39 | 0.00% | FAIL | pass |
| cbBTC/PYUSD | 25% | 0.62 | 0.11% | FAIL | pass |
| sUSDat/AUSD | 25% | 0.85 | 0.01% | FAIL | pass |
| PT-reUSD-25JUN2026/USDC | 5% | 1.18 | 0.00% | pass | pass |

Latent insolvency = debt not covered by collateral on stressed oracle terms (Morpho.sol exhaustion condition), independent of keeper execution.

#### Documented exclusions

* **sUSDS/USDT**: no slippage curve (unusable quotes (7/7 positive-bps rows))
* **msY/USDC**: no oracle price series (oracle interface not supported this window)
<!-- END GENERATED: report_results -->

### 4.5 The Monte Carlo companion: realized versus latent

Two probabilities are reported per market over the empirical 24-hour
drawdown distribution of its own oracle window (200 paths, seed 42):

* **Realized bad debt** through the v1.1 liquidation engine. Under deep
  slippage the keeper-rationality gate produces a keeper strike (no
  execution), so realized bad debt is structurally near zero in stress:
  this measures what the contract would book, not what the market owes.
* **Latent insolvency**: debt not covered by collateral on stressed oracle
  terms (the Morpho.sol exhaustion condition), computed analytically and
  therefore immune to the keeper-strike regime. This is the solvency leg
  that the tables report.

---

## 4bis. Extreme stress test

### 4bis.1 Calibration

Outflow alpha is set to 35% (the KelpDAO + USDC-depeg hybrid anchor). The
price shock is class-aware: 25% for volatile collateral, and for markets
whose window-worst 24-hour drawdown is below 3% (redemption-arbitraged
correlated pairs and yield-bearing stables) the shock is capped at three
times the worst observed move, floored at 5%; a 25% shock on a
redemption-arbitraged ratio would not be an economic scenario. The drawdown
actually applied is reported per market.

### 4bis.2 Survival criterion, two legs

A market fails the extreme test if either leg fails:

* **Illiquidity leg**: LSR under the shocked oracle and 35% outflows falls
  below 1.
* **Solvency leg**: latent insolvency exceeds 10% of supply.

Reporting the legs separately is the point: a market can be illiquid and
solvent, and on current books that is exactly what happens.

### 4bis.3 Result

See the extreme-scenario table in section 4.4 (generated block). The
headline is the dichotomy itself: at this snapshot the extreme
scenario fails on the liquidity leg across the overwhelming majority
of evaluated markets and supply, and on the solvency leg nowhere; the
generated table carries the exact counts.


## 4ter. MetaMorpho vault curator discipline

Deferred. The v1.0 vault-curator analysis predates the v1.1 engine and
is superseded; it is retained for historical reference in
`docs/archive/metamorpho_v1.0.md`. A regenerated curator analysis will
follow as a separate publication.

## 4quater. What changed versus v1.0, and why the panorama moved

The v1.1 engine applies the corrections catalogued in
[docs/MODEL_CORRECTIONS.md](MODEL_CORRECTIONS.md) (C1 to C7), and the
evaluation chain replaces two v1.0 inputs wholesale:

* **Real position books instead of synthetic ones.** v1.0's forward
  panorama drew position-level loan-to-values from a Beta-scaled synthetic
  distribution (average 0.65 x LLTV by construction). v1.1 evaluates the
  actual onchain positions served by the Morpho API, with per-market
  borrow-share coverage checked against market state.
* **Measured exit depth instead of class defaults.** v1.0 priced exotic
  collateral with asset-class default slippage parameters. v1.1 fits
  power-law curves on quoted depth: Uniswap V3 for majors, keyless
  aggregator quotes (CoW Protocol, KyberSwap) rebased on the smallest
  executed size for yield-bearing wrappers, and a conservative flat
  fallback for venues too deep to move.

Directionally, three v1.0 artefacts inflated resilience: liquidation
recoveries were double-counted in the coverage ratio (C6), non-callable
healthy debt was counted as monetisable stock (C4), and synthetic books
were more conservative than the real ones in some markets and less in
others. The v1.0 finding that no market breached the coverage threshold
does not survive these corrections; the survival-frontier table above is
the corrected statement.

## 5. What this work does not establish

We list these explicitly because they materially affect the
interpretability of the headline numbers, and decentralised-finance
risk reporting often omits such caveats.

1. **Tail estimates ride on short windows and thin books.** The Monte
  Carlo samples each market's own 30-day drawdown distribution over
  the actual position book. 99th-percentile magnitudes therefore
  carry wide confidence intervals, especially for markets with few
  active positions (under 20) or quiet windows. Latent-insolvency
  figures are analytic given the shock; the shock distribution itself
  is window-bound.
2. **Counterfactual events are weakly identified.** The USDC and
  staked-Ether events predate Morpho Blue. We synthesised position
  distributions for them, calibrated to plausible parameters of
  current practice. The PASS verdict on the USDC event is more
  reliable than the FAIL verdict on the staked-Ether event because the
  USDC drawdown is large enough to drive a clear signal; the
  staked-Ether outcome depends on a distinction between 24-hour and
  multi-day stress that the framework was not designed to make.
3. **Keeper economics are modelled at the aggregate level only.** The
  engine gates liquidation on the profitability of the aggregate
  eligible batch at the aggregate slippage (all-or-none keeper
  strike); per-liquidator gas competition, partial fills and
  maximal-extractable-value ordering are not modelled. The all-or-none
  convention is conservative on recoveries, which is why latent
  insolvency is reported alongside realized bad debt.
4. **Endogenous oracle feedback is partially modelled.** Exogenous
  oracles (Chainlink, Pyth, Redstone) are handled correctly:
  liquidator selling does not affect the oracle. Time-Weighted
  Average Price oracles from Uniswap V3 receive endogenous
  decentralised-exchange-price propagation through the time-weighted
  average smoothing, but the current framework does not solve the
  within-block fixed point implied by full liquidation cascades; we
  model sequentially within each block.
5. **Three events is a small sample for backtest validation.**
  Statistical significance is not claimed; the two-of-three pass
  rate is illustrative of the framework's discrimination, not a
  frequentist guarantee.
6. **The panorama is a photograph, not a monitor.** Positions, market
  state and depth quotes are read live from the chain and public
  interfaces, then frozen at the stamped snapshot; nothing here
  refreshes continuously, and depth-venue coverage per snapshot is
  whatever the quote cache holds.
7. **No rate-driven replenishment.** Borrowers repaying into a
  spiking rate curve, the main real-world stabiliser of a withdrawal
  run, is deliberately not modelled; survival frontiers are lower
  bounds in that respect.
8. **The empirical outflow alpha is discontinuous** at its 5%
  large-holder trigger: two otherwise similar markets can carry very
  different markers. The survival frontier, a continuous quantity,
  carries the verdict for exactly this reason.
9. **Measured depth is conservative for instantly-redeemable
  wrappers** (arbitrageurs can mint and redeem at net asset value);
  for cooldown wrappers such as sUSDe, the measured curve is the
  24-hour exit.

---


## 6. Reproducibility

The full v1.1 chain, from empty cache to this document's figures:

```
python scripts/fetch_markets.py
python scripts/fetch_tvl.py
python scripts/fetch_market_state.py
python scripts/fetch_oracle_prices.py
python scripts/fetch_events.py            # optional for the evaluation
python scripts/fetch_positions_api.py     # live position book
python scripts/fetch_uniswap_quotes.py    # majors depth
python scripts/fetch_agg_quotes.py        # exotic depth, keyless
python scripts/run_evaluation.py          # -> docs/evaluation_results.csv
python scripts/generate_report_tables.py  # -> docs/_generated/*.md
python scripts/assemble_docs.py           # splices figures into the docs
```


The full pipeline is open-source. Key features:

- **Versioned event fixtures** under `data/fixtures/<event-id>/` with
  per-row source attribution, reproducible from the fixture
  generation script.
- **145 unit and property-based tests** with the `pytest` and
  `hypothesis` libraries.
- **Demonstration notebooks** for each phase of the work, runnable
  with the command `PYTHONPATH=src python notebooks/phase{N}_demo.py`.
- **Strict typed schemas** (using PyArrow and Pandera) gate every
  Parquet write, preventing silent type drift between data and model.
- **Manifest-tracked runs** with configuration hashes for full
  pipeline reproducibility.

The repository structure, methodology, scenario specification, data
architecture, and backtest specification are documented in the files
[`METHODOLOGY.md`](./METHODOLOGY.md), [`SCENARIOS.md`](./SCENARIOS.md),
[`DATA.md`](./DATA.md), and [`BACKTEST.md`](./BACKTEST.md).

---

## 7. References

Selected anchors. The full bibliography is in
[`references.md`](./references.md); definitions of all institutional
and on-chain terms are in [`GLOSSARY.md`](./GLOSSARY.md).

- Bank for International Settlements. *Basel III: The Liquidity
  Coverage Ratio and liquidity risk monitoring tools.*
  Publication BCBS 238, 2013.
- Bank for International Settlements. *Basel III: The Net Stable
  Funding Ratio.* Publication BCBS 295, 2014.
- Chiu, J., Ozdenoren, E., Yuan, K., Zhang, S. *On the inherent
  fragility of decentralised-finance lending.* Bank for International
  Settlements Working Paper 1062, 2023.
- Gudgeon, L., Werner, S. M., Perez, D., Knottenbelt, W. J.
  *Decentralised-finance protocols for loanable funds.* Financial
  Cryptography 2020.
- Almgren, R., Chriss, N. *Optimal execution of portfolio
  transactions.* Journal of Risk, 2000.
- Morpho Labs. *Morpho Blue Whitepaper* and *Morpho Blue Yellow
  Paper*, 2024.

---

## 8. About this work

This is an independent research project. It has no affiliation with
Morpho Labs or any MetaMorpho vault curator. It is not investment
advice, not a security audit, and not a substitute for production
risk monitoring.

Feedback, corrections, and counter-arguments are welcome. The
repository accepts pull requests and issues.
