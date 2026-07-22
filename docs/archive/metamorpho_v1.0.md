# MetaMorpho vault curator discipline (v1.0, superseded)

> **Superseded methodology, retained for historical reference only.**
> Figures below come from the v1.0 vault enrichment run and predate
> the v1.1 engine; they are excluded from the v1.1 publication scope.

> **Status**: the figures in this section come from the v1.0 vault
> enrichment run. Regenerate via `scripts/fetch_metamorpho_vaults.py` and
> `scripts/generate_visualizations.py` before publication, or defer this
> section to a follow-up post.

### 4ter.1 Motivation

Beyond per-market analysis, a natural application of the tier
classification is to score the **discipline of MetaMorpho vault
curators**: how exposed is each vault to markets that the framework
classifies as red, yellow, green-watch, or green-strong? The output
is not a verdict on curator quality (a curator may legitimately
allocate to higher-tier markets if they have priced in the risk) but
a quantitative breakdown that supports comparability across curators.

### 4ter.2 Methodology

For each MetaMorpho vault, we extract the supply allocations across
markets via the Morpho API and compute a TVL-weighted **curator
discipline score**:

$$\text{score} = \sum_{m \in \text{allocations}} \frac{\text{supply}_m}{\text{TVL}_{\text{vault}}} \cdot w(\text{tier}_m)$$

where the tier weights $w$ are: red $= 4$, yellow $= 2$, green-watch
$= 1$, green-strong $= 0$. Allocations to markets outside our 26-
market roster (typically smaller markets, EUR-stablecoin markets, or
chains other than Ethereum) are bucketed as `unknown` and do not
contribute to the score.

The score interpretation is:

- $0.0$, perfectly conservative: vault is fully invested in markets
  the framework classifies as green-strong.
- $\sim 1.0$, moderate discipline: vault has meaningful exposure to
  green-watch markets and small yellow exposure.
- $\sim 2.0$, significant yellow exposure: vault is allocating to
  yellow-tier markets that carry material absolute tail risk.
- $> 2.0$, substantial red/yellow exposure that warrants curator-side
  review.

### 4ter.3 Result

Applied to the top 20 MetaMorpho vaults by TVL on Ethereum mainnet:

| Vault | Asset | TVL ($M) | Score | red% | yellow% | green-watch% | green-strong% | unknown% |
|---|---|---|---|---|---|---|---|---|
| Sentora PYUSD | PYUSD | 244.5 | 0.56 | 0.0 | 8.8 | 38.5 | 35.4 | 17.3 |
| Sentora RLUSD | RLUSD | 166.0 | 0.00 | 0.0 | 0.0 | 0.0 | 61.0 | 39.0 |
| Gauntlet USDC Prime | USDC | 150.9 | 2.00 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Steakhouse USDC | USDC | 129.4 | 1.94 | 0.0 | 96.8 | 0.0 | 0.0 | 3.2 |
| Steakhouse USDT | USDT | 125.2 | 1.77 | 0.0 | 82.9 | 11.7 | 0.0 | 5.4 |
| Steakhouse Ethena USDtb | USDtb | 85.2 | 0.00 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 |
| Steakhouse EURCV | EURCV | 51.2 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 |
| Sentora PYUSD Core | PYUSD | 50.2 | 1.01 | 0.0 | 1.5 | 98.5 | 0.0 | 0.0 |
| Vault Bridge USDC | USDC | 48.9 | 2.00 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Gauntlet WETH Prime | WETH | 42.1 | 0.99 | 0.0 | 0.0 | 98.7 | 0.0 | 1.3 |

The full table of 20 vaults is reproducible by running
`python scripts/fetch_metamorpho_vaults.py --top 20`.

### 4ter.4 Findings

**Finding 1: Cross-curator convergence on USDC vault strategy.** The
four largest USDC-asset vaults (Gauntlet USDC Prime, Steakhouse USDC,
Vault Bridge USDC, Hakutora USDC) all converge on a curator score of
approximately 2.0, reflecting a near-exclusive allocation to the
yellow tier. This is not a quality differentiator: it is a
**structural feature** of the USDC vault product. The yellow tier
contains the four mainstream BTC/ETH-collateral markets (cbBTC/USDC,
WBTC/USDC, wstETH/USDT, wstETH/USDC) which represent the bulk of USDC
yield-bearing supply on Morpho Blue. Any USDC vault providing
competitive net APY must be exposed to these markets.

The finding therefore is not "Steakhouse and Gauntlet are aggressive"
but rather "**the USDC product structurally concentrates the protocol's
material tail risk** in a small number of mainstream markets". The
risk is not idiosyncratic to any one curator.

**Finding 2: Differentiated discipline across asset classes.** USDC
vaults converge at score $\approx 2.0$. PYUSD and stablecoin-synthetic
vaults are more diversified: Sentora PYUSD has a score of 0.56 with
33% green-strong allocation; Smokehouse vaults distribute across many
small markets (22+ allocations). RLUSD-asset vaults (Sentora RLUSD)
score 0.0, reflecting a pure allocation to the green-strong
syrupUSDC/RLUSD market.

**Finding 3: Scope limitation: 100% unknown vaults.** Three vaults
in the top 20 score 0.0 with 100% unknown classification: Steakhouse
EURCV, Vault Bridge WBTC, and Adpend USDC. The first two allocate to
markets outside our 26-market USD-denominated roster (EUR-stablecoin
markets and smaller WBTC markets respectively); the third uses 30
small allocations spread across long-tail markets we did not fetch.
The framework provides no useful information for these vaults at the
current roster size.

### 4ter.5 Limitations

- **The score weights are arbitrary**: red = 4 reflects an editorial
  choice that a red allocation is twice as concerning as a yellow.
  A different weighting scheme would produce different rankings.
  We provide the per-tier breakdown alongside the score so
  consumers can re-weight for their own purposes.
- **Static snapshot**: vaults rebalance, often daily. The score is
  point-in-time. A production deployment would compute the score
  weekly and track its evolution per vault.
- **Curator intent is not modelled**: a vault can intentionally hold
  yellow-tier exposure if it has priced in the risk through a higher
  expected yield, a withdrawal queue, or a guarantor backstop. The
  framework reports tier exposure; it does not determine whether that
  exposure is appropriate.

---
