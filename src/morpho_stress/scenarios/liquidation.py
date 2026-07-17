"""Liquidation engine.

Models Morpho Blue's liquidation logic (v1.1, contract-faithful accounting):

1. A position is liquidatable iff its LTV exceeds the market's LLTV.
2. The liquidator repays debt and seizes collateral on ORACLE terms with the
   incentive multiplier (LIF): seized = repaid * LIF / oracle_price.
3. Bad debt is realised ONLY when the position's collateral is exhausted and
   debt remains (Morpho.sol semantics); it is then socialised against the
   supplier pool. The liquidator's DEX resale (market price, slippage) drives
   liquidator PROFITABILITY, never pool bad debt.
4. If the position is closed with collateral to spare, the residual collateral
   stays with the borrower (the position remains, debt-free) rather than
   evaporating from the market aggregates.

Reference:
    - Morpho Labs, Morpho Blue Whitepaper §6 (Liquidations)
    - On-chain: `Morpho.liquidate(MarketParams, borrower, seizedAssets, repaidShares, data)`

Simplifications vs on-chain (see docs/MODEL_CORRECTIONS.md):
    - No callback (no MEV / flashloan-funded liquidator modeling)
    - Liquidations are immediate within the block (no mempool delay)
    - Liquidator always liquidates the maximum allowed amount (close factor = 1)
    - Keeper rationality is enforced at the batch level: if the aggregate DEX
      resale of the whole eligible set is unprofitable at the aggregate
      slippage, no liquidation executes this step (keeper strike). A partial
      fill search (largest profitable volume) is a planned refinement.
"""

from __future__ import annotations

from dataclasses import dataclass

from morpho_stress.models.constants import EPS
from morpho_stress.models.slippage import SlippageCurve
from morpho_stress.scenarios.state import MarketState, Position


@dataclass(frozen=True, slots=True)
class LiquidationOutcome:
    """Result of a single position's liquidation."""

    borrower: str
    repaid_assets: float  # loan asset paid back
    repaid_shares: float
    seized_collateral: float
    realized_loan_value: float  # liquidator's DEX resale proceeds (diagnostics)
    bad_debt_assets: float  # debt written off on collateral exhaustion (Morpho.sol semantics)


def liquidation_incentive_factor(lltv: float) -> float:
    """Morpho Blue's LIF formula.

    LIF = min(M, 1 / (β * LLTV + (1 - β)))
    where β = 0.3, M = 1.15

    For LLTV = 0.86, LIF ≈ 1.043 (the canonical 4.3% bonus).
    """
    beta = 0.3
    m_cap = 1.15
    return min(m_cap, 1.0 / (beta * lltv + (1.0 - beta)))


def liquidate_position(
    state: MarketState,
    position: Position,
    market_price: float,
    slippage_curve: SlippageCurve,
    realized_price: float | None = None,
) -> tuple[LiquidationOutcome, MarketState]:
    """Liquidate a single position fully and return updated state.

    Contract-faithful mechanics (Morpho.sol):
        1. Full close: the liquidator targets the entire debt b.
        2. Seizure on ORACLE terms: desired_seize = b * LIF / oracle_price,
           capped at the position's collateral.
        3. If collateral covers the seizure, repaid = b, no bad debt, and the
           residual collateral stays with the borrower (position kept with
           zero debt).
        4. If collateral is exhausted, repaid = seized * oracle_price / LIF,
           and the shortfall b - repaid is realised as bad debt, socialised
           against the supplier pool; the position is removed.

    The DEX resale (`market_price`, slippage) is the LIQUIDATOR's side: it is
    reported in the outcome for profitability analysis and never creates pool
    bad debt. `realized_price`, when given, overrides the per-position curve
    price with a batch-level aggregate price (see liquidate_all_eligible).

    Returns:
        (outcome, new_state)
    """
    repaid_shares = position.borrow_shares
    debt = position.borrow_assets(
        state.total_borrow_assets, state.total_borrow_shares
    )

    if debt < EPS:
        # Nothing to liquidate: position has zero debt, nothing changes
        return (
            LiquidationOutcome(
                borrower=position.borrower,
                repaid_assets=0.0,
                repaid_shares=0.0,
                seized_collateral=0.0,
                realized_loan_value=0.0,
                bad_debt_assets=0.0,
            ),
            state,
        )

    lif = liquidation_incentive_factor(state.params.lltv)
    desired_seize = debt * lif / state.oracle_price
    seized = min(desired_seize, position.collateral)

    if seized >= desired_seize - EPS:
        # Collateral covers the full seizure: whole debt repaid, no bad debt
        repaid_assets = debt
        bad_debt = 0.0
        residual = position.collateral - seized
        others = tuple(
            p for p in state.positions if p.borrower != position.borrower
        )
        if residual > EPS:
            import dataclasses as _dc
            new_positions = others + (
                _dc.replace(position, collateral=residual, borrow_shares=0.0),
            )
        else:
            new_positions = others
    else:
        # Collateral exhausted: partial repayment, shortfall becomes bad debt
        repaid_assets = seized * state.oracle_price / lif
        bad_debt = max(0.0, debt - repaid_assets)
        new_positions = tuple(
            p for p in state.positions if p.borrower != position.borrower
        )

    # Liquidator's resale (diagnostics / profitability, not pool accounting)
    if realized_price is None:
        realized_price = slippage_curve.realized_price(seized, market_price)
    realized_loan_value = seized * realized_price

    new_borrow_assets = max(0.0, state.total_borrow_assets - debt)
    new_borrow_shares = max(0.0, state.total_borrow_shares - repaid_shares)
    new_collateral = max(0.0, state.total_collateral - seized)
    new_supply_assets = max(0.0, state.total_supply_assets - bad_debt)

    new_state = state.replace(
        positions=new_positions,
        total_borrow_assets=new_borrow_assets,
        total_borrow_shares=new_borrow_shares,
        total_collateral=new_collateral,
        total_supply_assets=new_supply_assets,
        realized_bad_debt=state.realized_bad_debt + bad_debt,
    )

    return (
        LiquidationOutcome(
            borrower=position.borrower,
            repaid_assets=repaid_assets,
            repaid_shares=repaid_shares,
            seized_collateral=seized,
            realized_loan_value=realized_loan_value,
            bad_debt_assets=bad_debt,
        ),
        new_state,
    )


def liquidate_all_eligible(
    state: MarketState,
    market_price: float,
    slippage_curve: SlippageCurve,
) -> tuple[list[LiquidationOutcome], MarketState]:
    """Liquidate every liquidatable position at the current oracle price.

    The DEX impact of aggregate selling is computed ONCE on the total seized
    volume: every position's resale is priced at the aggregate realized price
    realized_price(V_total). This matters under endogenous regimes (S4) where
    the cumulative impact is what moves the oracle.

    Keeper rationality gate: on Morpho terms, repaid/seized = oracle/LIF is
    identical across positions of a market, so at a uniform aggregate price the
    batch is either profitable for all or for none. If the aggregate resale
    cannot cover the aggregate repayment (deep slippage), no rational keeper
    executes and no liquidation happens this step (keeper strike); the eligible
    debt stays outstanding.
    """
    eligible = state.liquidatable_positions()
    if not eligible:
        return [], state

    lif = liquidation_incentive_factor(state.params.lltv)
    total_seize = 0.0
    total_repaid = 0.0
    for pos in eligible:
        debt = pos.borrow_assets(state.total_borrow_assets, state.total_borrow_shares)
        seize = min(debt * lif / state.oracle_price, pos.collateral)
        total_seize += seize
        total_repaid += min(debt, seize * state.oracle_price / lif)

    if total_seize < EPS:
        return [], state

    agg_price = slippage_curve.realized_price(total_seize, market_price)

    if agg_price * total_seize < total_repaid:
        # Keeper strike: aggregate resale does not cover aggregate repayment
        return [], state

    outcomes: list[LiquidationOutcome] = []
    new_state = state
    for pos in eligible:
        outcome, new_state = liquidate_position(
            new_state, pos, market_price, slippage_curve,
            realized_price=agg_price,
        )
        outcomes.append(outcome)

    return outcomes, new_state
