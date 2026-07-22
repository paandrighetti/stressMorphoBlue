# Model corrections from v1.0 to v1.1

The published v1.1 engine applies contract-aligned corrections identified during an
adversarial review. Each row records the v1.0 behaviour, the bias it introduced,
and the corresponding v1.1 correction now implemented in the code. The committed
v1.1 headline tables were generated from the corrected engine for the published
snapshot. Historical v1.0 figures are retained only where explicitly marked as
archived or superseded.

| # | Component | v1.0 behaviour | Bias of v1.0 | v1.1 correction (applied) |
|---|-----------|----------------|--------------|---------------------------|
| C1 | `liquidation` | Bad debt booked as debt minus the liquidator's modelled DEX resale proceeds. | Overstated bad debt and red flags; could book pool losses on fully repaid positions. | Bad debt realised only on collateral exhaustion (Morpho.sol semantics); DEX resale drives liquidator profitability only. |
| C2 | `liquidation` | Position removed entirely while only the seized collateral left the aggregates (phantom collateral). | State violated market invariants after partial seizures. | Residual collateral stays with the borrower: position kept, debt-free. |
| C3 | `liquidation` | Docstring claimed aggregate DEX impact; code repriced each position independently. | Understated cumulative impact on convex curves. | Aggregate volume priced once; uniform realized price applied to the batch. Keeper-rationality gate: unprofitable batches do not execute (keeper strike). |
| C4 | `liquidity_metrics` | Recovery function seized on MARKET price and passed resale proceeds through as pool recovery; healthy positions counted as recoverable. | Mixed liquidator and pool accounting; non-callable debt counted as monetisable. | Seizure on oracle terms; recovery = repaid; executability gate at stress prices; only liquidatable positions enter the stock. |
| C5 | `irm` | Supply accrued interest*(1-fee); drift error normalised by max(t, 1-t); interest at start-of-interval rate. | Understated supply liquidity; above-target adaptation ~9x too slow at 90% target (anti-conservative on stress rates); interval rate off. | Full interest to supply; piecewise normaliser; average rate-at-target (start+end+2*mid)/4 as in AdaptiveCurveIrm.sol. |
| C6 | `liquidity_metrics` | Liquidation recoveries counted in the numerator AND netted from outflows. | Same unit improved the ratio twice: **anti-conservative**, inflated LSR-24. | Single-counted: numerator only. |
| C7 | `liquidity_metrics` | Division floor of 1.0 loan-asset unit, not scale-invariant. | Edge distortion for low-outflow or high-unit-value markets. | Relative epsilon on total supply. |

Remaining known simplifications: exact exponentials and float64 instead of
WAD/Taylor fixed-point; fee-recipient supply shares aggregated; close factor 1
per position with a batch-level keeper strike instead of a partial-fill search;
no mempool latency.

## Historical release checklist

The following release checklist is retained verbatim for methodological provenance.
Its imperative wording records the original release process and does not represent
pending publication work.
1. Re-fetch the market snapshot (26 markets) with the pipeline scripts.
2. Regenerate REPORT.md tables, README headline block and the Mirror article
   figures with the v1.1 engine.
3. Update the Dune dashboard queries/numbers where they mirror engine outputs.
4. Re-check the three historical event fixtures: flags may legitimately change
   under C5/C6 (both corrected biases were optimistic); report the v1.1 labels.
5. Add differential tests against Morpho.sol and AdaptiveCurveIrm.sol
   behaviour on recorded mainnet transactions (backlog).

## Evaluation-chain changes (beyond the engine)

Alongside C1 to C7, the v1.1 evaluation chain replaced two v1.0 inputs
wholesale: position books are the actual onchain positions served by the
Morpho API (per-market borrow-share coverage checked against market
state) instead of Beta-scaled synthetic distributions, and exit depth is
measured (Uniswap V3 quoter; keyless CoW Protocol and KyberSwap quotes
rebased on the smallest executed size; a Pendle-router conversion path for principal tokens, unused at the first v1.1 snapshot because the roster's PTs are past maturity) instead of asset-class default parameters. The
panorama's primary metric became the survival frontier alpha\*, and all
published figures flow through `run_evaluation.py`,
`generate_report_tables.py` and `assemble_docs.py` without manual
transcription.
