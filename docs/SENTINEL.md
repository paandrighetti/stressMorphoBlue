# Daily liquidity sentinel

The framework of this repository measures, for each Morpho Blue market of the roster, the largest
share of supply the market can pay out within 24 hours under stress (alpha*, see
[METHODOLOGY.md](METHODOLOGY.md)). The published evaluation is a snapshot. The sentinel repeats it
every day on live data and turns it into the risk-reducing actions that Morpho's vaults allow:
the sentinel role of a Vault V2, or the guardian, curator and allocator of a MetaMorpho (V1) vault.

It is read-only. It never signs a transaction, and its list is advice for the people who hold those
roles. Results: the [sentinel-data branch](https://github.com/paandrighetti/stressMorphoBlue/tree/sentinel-data)
(`latest.md`, `history.csv`, and the day's evaluation, allocations and actions under dated names).

## 1. What runs each day

1. `scripts/sentinel_config.py` writes the run's configuration: the roster of `markets_top.yaml`,
   the sampling cadences of `config.yaml` (those of the published evaluation), a window of the last
   30 days, and an Ethereum endpoint that serves historical state.
2. The fetch pipeline of [REPORT.md](REPORT.md) (markets, market state, oracle prices, position book,
   Uniswap and keyless aggregator quotes), unchanged.
3. `scripts/run_evaluation.py`, unchanged: alpha*, tier, and the companion metrics per market.
4. `scripts/run_sentinel.py`: the vaults' allocations to the roster from the Morpho API, the rule of
   section 2, the report and the history.

The workflow is `.github/workflows/sentinel.yml` (05:23 UTC).

## 2. The rule

Notation, all amounts in units of the market's loan asset:

- S: the market's supply, U: its utilization, alpha*: its survival frontier and tier of the day
  (red below 10%, yellow below 30%, green otherwise; thresholds of the published framework).
- Absorbable outflow A = alpha* x S: what the market pays out within 24 hours under the stress.
- For a vault with allocation a in the market: coverage = A / a. Below 1, the vault could not
  withdraw all of its allocation within 24 hours under the stress, even first in line.
- Idle liquidity L = S x (1 - U): what a withdrawal can take now, before any repayment.

Actions, for each vault and each market of the roster it supplies:

| Market tier | Condition | Action | Amount |
|---|---|---|---|
| red | a cap increase is pending | revoke the pending cap | the pending cap |
| red | coverage below 1 and cap above the allocation | decrease the cap to the allocation | a |
| red | coverage below 1 | deallocate | min(a, L) |
| yellow | the pending cap exceeds A | revoke the pending cap | the pending cap |
| green | | none | |

Roles and calls: on a Vault V2, the sentinel's `revoke`, `decreaseAbsoluteCap` and `deallocate`; on a
MetaMorpho vault, the guardian's `revokePendingCap`, the curator's `submitCap` (a decrease applies
at once) and the allocator's `reallocate`.

Why the coverage condition. Morpho's adaptive interest rate model steers utilization towards 90%, so
for most markets alpha* sits near 1 - U, that is near the red threshold of 10%: a market moves
between red and yellow on small changes of utilization. A vault whose allocation is small compared
with the market's absorbable outflow can exit even when the market is red; the actions that cost
yield (freezing the cap, withdrawing) are kept for the vaults that could not.

The report also gives, for each market, its tier at the previous run and the number of consecutive
runs in its tier, so a reader can tell a new red from a persistent one.

## 3. Data and endpoints

No key is needed. The position book and the vaults come from the Morpho API
(`https://api.morpho.org/graphql`), whose queries are built from the live schema; a field the API
does not expose leaves the corresponding amount unknown, and the report says which fields were used.
Exit depth comes from the Uniswap V3 quoter and the keyless CoW Protocol and KyberSwap quote
endpoints. The market state and oracle samplers read historical state, which needs an archive node:
the run uses the repository secret `ALCHEMY_KEY` when it is set, and otherwise the first public
endpoints that answer an archive read at the start of the window.

## 4. Limitations

- Daily cadence: an event inside a day is seen at the next run. The sentinel complements, and does
  not replace, the real-time monitoring of oracle and governance events.
- The stress is the framework's: a 24-hour window, the worst oracle price of the last 30 days, the
  measured exit depth of the day. It does not model the interest rate model's response, which draws
  liquidity back within hours (the time-to-illiquid metric of the evaluation covers part of it).
- Coverage assumes the vault is first in line. With several vaults withdrawing at once, each gets
  less; a coverage just above 1 is not a guarantee.
- Vault V2 allocations are read only when the API exposes per-market caps; the report states whether
  they were covered.
- Markets without a measured exit-depth curve, an oracle series or a position book that day are
  listed as not evaluated, with the reason.
