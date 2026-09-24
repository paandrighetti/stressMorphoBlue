# Protocol fees and revenue

Daily fees and revenue of the 26 monitored Morpho Blue markets, in Token Terminal's metric
definitions. They are built in the dbt project (`dbt/`) from the Parquet cache of the stress
framework. Two reference files in `docs/benchmarks/` serve the comparison of section 5: DefiLlama's
daily fees and Morpho's market listing. The results are in
[`docs/_generated/fees_snapshot.md`](./_generated/fees_snapshot.md), written by
`dbt/scripts/export_fees_snapshot.py`; this note gives the method.

## 1. Metrics

Token Terminal defines fees as what users pay to use an application (interest paid by borrowers,
for a lending protocol) and revenue as the part of fees the project keeps through its take rate.
The rest of the fees goes to the supply side: lenders, liquidity providers.

| Metric | Morpho Blue (`Morpho.sol`) | Column of `mart_protocol_fees_daily` |
|---|---|---|
| Fees | Interest booked on borrowers' debt by `_accrueInterest` | `fees_loan_units` |
| Revenue | Interest times the market fee, minted as supply shares to the fee recipient | `revenue_loan_units` |
| Supply-side fees | Fees minus revenue, credited to suppliers' balances | `supply_side_fees_loan_units` |
| Liquidation incentive | Collateral seized above the debt repaid, `repaid * (LIF - 1)` | `liquidation_incentive_loan_units` |
| Stuck interest | Interest booked while a market sits at full utilization (section 3) | `stuck_interest_loan_units` |

LIF is the liquidation incentive factor. `liquidate` in `Morpho.sol` computes it as
`min(1.15, 1 / (0.3 * LLTV + 0.7))`, with LLTV the market's liquidation loan-to-value and the two
constants in `ConstantsLib.sol`. The liquidated borrower pays the incentive to the liquidator.
Keeping it out of fees is a choice of scope, so that fees stay a pure interest figure; DefiLlama
adds it to fees, and section 5 uses its definition for the comparison.

The grain is one row per UTC day and market. Amounts stay in the market's loan asset and are never
added across loan assets; the snapshot prints USD-stable loans in dollars at par and WETH loans in
WETH.

## 2. Interest from two ledgers

The cache holds contract state reads (`market(id)` through `eth_call`, every 1,800 blocks, about
six hours) and the market events. Over the blocks between two reads of a market, the contract's
accounting gives:

```
borrow ledger   B1  = B0  + borrowed - repaid - liquidation repaid - bad debt + interest
supply ledger   S1  = S0  + supplied - withdrawn - bad debt + interest
supply shares   SS1 = SS0 + shares supplied - shares withdrawn + fee shares
```

Each asset ledger yields the interest on its own, from two state reads and the events in between
(`int_morpho__interest_intervals`). The published figure comes from the borrow ledger, whose totals
are smaller; the supply ledger is the check. A missing or duplicated event moves one ledger and not
the other. The check cannot see errors that move both ledgers by the same amount: a supply and a
borrow of equal size both missing or both duplicated, the same for a withdrawal and a repayment
(or a liquidation's repayment), or a wrong bad-debt amount, which enters both ledgers. The share
ledger gives the fee shares actually minted, which tests the revenue figure against the contract.

This does not rebuild a balance from flows (rule 2 of `dbt/README.md`): balances remain the state
reads, and flows only explain the change between two reads.

The daily series follows booking. The contract books interest only when a transaction touches the
market, and a state read returns the stored totals, so an interval without such a transaction
shows zero interest and the next one books the catch-up. A market that nobody touches for several
days books them all on one day. Series built from `AccrueInterest` events, such as DefiLlama's,
follow the same booking, which keeps the comparison of section 5 on one basis. The reads place
each booking within about six hours.

An interval counts only if it lies between the first and the last cached event, since the event
cache spans one fetch window for every market. The first and last days of the window are therefore
partial (`day_coverage` below 1), and the snapshot keeps full days only.

Each interval's interest is spread over UTC days pro rata to its seconds in each day.
`dbt/profiles.yml` sets the DuckDB session to UTC; DuckDB otherwise truncates timestamps to days in
the machine's time zone.

## 3. Stuck markets

An interval whose market has a utilization of at least 0.999 at both reads (dbt var
`stuck_utilization`) is flagged `is_stuck`, and its interest goes to `stuck_interest_loan_units`
rather than to fees. At full utilization Morpho's adaptive rate model (the AdaptiveCurveIRM
contract, modelled in `src/morpho_stress/models/irm.py`) keeps raising the rate, and the interest
that `Morpho.sol` books raises suppliers' claims while no cash is left to withdraw at the reads.
Such interest is a claim whose payment the data does not show, so it is reported apart. A short
spike to 100 % does not trigger the rule, since both reads must be at the threshold; a healthy
market pinned at full utilization for two reads in a row would be flagged, which lowers fees
rather than inflating them.

In the window, the rule flags one market, msY/USDC (`0x23a7d0ff`). Its borrowers made their last
repayment of the window two days after it reached full utilization, and interest then kept
compounding on the debt at a rate of several hundred percent a year (snapshot, "Stuck markets").
It was already excluded from the stress publication, for lack of an oracle price series. Morpho's
API does not list it and flags it `oracle_unusable` and `sustained_low_liquidity`
(`docs/benchmarks/morpho_api_market_listing.csv`, queried on 2026-09-24).

## 4. Checks

Tests run by `dbt build`, on the real cache and in CI:

| Test | What fails it |
|---|---|
| `assert_interest_ledgers_agree` | Borrow and supply ledgers differ by more than 1e-9 of the supply on a covered interval |
| `assert_interest_not_negative` | Negative interest beyond float64 rounding (borrow rates are never negative) |
| `assert_fee_shares_match_fee` | Fee shares minted and interest times fee differ by more than 1 % (shares are valued at the end-of-interval price, not the price at minting) |
| `assert_fees_daily_conserve_interest` | The day split creates or loses interest |
| `assert_fees_daily_one_row_per_day_and_market` | Duplicate rows at the mart's grain |
| Unit test `interest_from_the_borrow_and_the_supply_ledgers` | Wrong ledger arithmetic, interval bounds, coverage or stuck flag, on mocked inputs |
| Unit test `fees_split_across_utc_days_pro_rata` | Wrong day split, stuck or coverage handling, or LIF, on mocked inputs |

The CI cache (`dbt/scripts/build_fixture_cache.py`) replays simulated flows, liquidations and
interest on a ledger that follows the contract's accounting (`MarketLedger`), with a 10 % fee on
one market so that the revenue path runs. The dbt run on it exercises the same identities as the
real cache.

The liquidation incentive uses the contract's own relation rather than cached prices: `liquidate`
sets `seized * oracle price = repaid * LIF` up to rounding, so `repaid * (LIF - 1)` is the
incentive at the price the contract used. The cached oracle series is sampled hourly and moves away
from that price during fast liquidation cascades.

## 5. Benchmark

DefiLlama publishes daily Morpho Blue fees per chain. The Ethereum series for the window is
committed in `docs/benchmarks/defillama_morpho_blue_ethereum_daily_fees.csv` (endpoint
`https://api.llama.fi/summary/fees/morpho-blue?dataType=dailyFees`, field
`totalDataChartBreakdown`, key `Ethereum`, retrieved on 2026-09-24).

The two series are not meant to match. DefiLlama's adapter counts only the markets that Morpho's
API lists at the time it runs, zeroes those its cache flags as stuck or insolvent, and values
tokens at market prices. This project covers 26 markets with stablecoins at par, three of which
Morpho's API did not list when queried on 2026-09-24: msY/USDC and two matured Pendle
principal-token markets. The comparison therefore checks scale only.

It also bounds what DefiLlama can contain: the stuck interest alone exceeds DefiLlama's total over
the same days, so DefiLlama's series cannot include all of it. An unlisted msY/USDC would explain
this, but the adapter reads the listing at each run, and the listing of June and July is not on
record here. DefiLlama's static blacklist entry for the market (a "fake USDC market") starts on
2026-07-21, after this window.

## 6. Limits

* Revenue is zero in the window because every market's fee is zero, as read from the contract and
  confirmed by the share ledger. Non-zero fees run only on the CI cache.
* When the fee changes inside an interval, revenue uses the fee at the start and the fee-share test
  skips the interval. No fee changed in the window.
* Daily figures follow booking, so they are uneven for markets that nobody touches for days. An
  accrual view is possible: the interest booked between two reads accrued exactly between their
  `Market.lastUpdate` values (`accrued_from_unix`, `accrued_to_unix`). It would smooth the days
  but leave the booking basis that DefiLlama and other `AccrueInterest` series use; both views
  miss the interest accrued after a market's last booking in the window.
* Stablecoins are valued at par and WETH is not converted.
* The scope is the 26 monitored markets, not the whole protocol. Vault fees (MetaMorpho
  performance fees) and token incentives are not measured, so there is no earnings line
  (Token Terminal's revenue minus token incentives).
* The stuck rule is a threshold: a market held at 99.8 % utilization for weeks would not be
  flagged.

## 7. Running it

```bash
cd dbt
dbt build --profiles-dir .                    # on the real cache, data/cache/*.parquet
cd ..
python dbt/scripts/export_fees_snapshot.py    # -> docs/_generated/fees_snapshot.md
```

## Sources

* Token Terminal, metric definitions: [Fees](https://tokenterminal.com/explorer/metrics/fees),
  [Revenue](https://tokenterminal.com/explorer/metrics/revenue).
* Morpho Blue contracts, `src/Morpho.sol` (`_accrueInterest`, `liquidate`) and
  `src/libraries/ConstantsLib.sol`: <https://github.com/morpho-org/morpho-blue>.
* Morpho API, fields `listed` and `warnings` of `markets`: <https://api.morpho.org/graphql>.
* DefiLlama fees adapter for Morpho, `fees/morpho/index.ts` (read at commit `65d7905`):
  <https://github.com/DefiLlama/dimension-adapters/blob/master/fees/morpho/index.ts>.
* DefiLlama API, daily fees for Morpho Blue: <https://api.llama.fi/summary/fees/morpho-blue?dataType=dailyFees>.
