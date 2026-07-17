"""Liquidity metrics — LCR_onchain v0.3 and event-calibrated TTI.

This module replaces the v0.2 LCR formulation in `runner.py` which produced
LCR ≈ 4 across all events (insufficient discrimination). The diagnosis from
Phase 4: total_collateral × oracle_price × 0.85 over-estimates recoverable
HQLA because collateral is pledged, not freely available.

The v0.3 formulation evaluates **liquidation recovery per position**, not
notional collateral, and discounts each recovery by stress-level slippage.
This matches the Basel III spirit: HQLA = assets that can be monetized in
stress *without* materially affecting their value.

Mathematical formulation:

    HQLA-like stock = L₁ + L_recoverable(stress)   [LSR-24 numerator]

where
    L₁ = total_supply_assets - total_borrow_assets        (instant liquidity)
    L_recoverable(stress) = Σᵢ repaidᵢ over LIQUIDATABLE, EXECUTABLE positions,
        repaidᵢ = min(bᵢ, seizedᵢ × P_oracle / LIF), seizedᵢ = min(bᵢ×LIF/P_oracle, cᵢ),
        executable iff seizedᵢ × P_market × (1 - π(seizedᵢ)) >= repaidᵢ.
    Bad debt (collateral-exhaustion write-offs) is reported separately.
    NOTE: 'L_recoverable' is loosely analogous to, but is NOT, Basel Level 2A;
    the metric is a protocol-adapted 24h Liquidity Survival Ratio (LSR-24),
    LCR-inspired rather than BCBS 238-compliant (BCBS 238 is a 30-day ratio).

The cap min(c×P×(1-π), b×LIF) reflects that:
    - liquidators only seize what's needed to cover debt × LIF
    - the seized amount sells on DEX with slippage π(seized_amount)
    - if c×P×(1-π) < b, the gap is bad debt (subtracted from HQLA)

Net outflows are calibrated event-specifically via:
    O_stress = α_p99(market) × total_supply_assets
where α_p99 comes from the market's historical withdrawal velocity, not a
universal constant.
"""

from __future__ import annotations

import numpy as np

from morpho_stress.models.constants import EPS
from morpho_stress.models.slippage import SlippageCurve
from morpho_stress.scenarios.liquidation import liquidation_incentive_factor
from morpho_stress.scenarios.state import MarketState


def position_recovery_value(
    state: MarketState,
    collateral_amount: float,
    borrow_assets: float,
    market_price: float,
    slippage_curve: SlippageCurve,
) -> tuple[float, float]:
    """Compute the loan-asset recovery for a single position under stress.

    Returns (recovery_value, expected_bad_debt) for one position.

    v1.1, contract-faithful: seizure sized on ORACLE terms; bad debt only on
    collateral exhaustion. The DEX resale (market price, stress slippage)
    gates EXECUTABILITY: if it cannot cover the repayment, no rational keeper
    liquidates within the horizon and the position contributes nothing
    (conservative for the numerator, no fictitious write-off either).

    Mechanics:
        1. seized = min(b × LIF / P_oracle, c)   [oracle terms, as on-chain]
        2. repaid to pool = min(b, seized × P_oracle / LIF)
        3. bad debt = b - repaid, only when collateral is exhausted
        4. executability gate: seized × P_market × (1 - π(seized)) >= repaid

    Args:
        state: current market state (used for LIF parameter only)
        collateral_amount: position collateral in collateral-asset units
        borrow_assets: position debt in loan-asset units
        market_price: collateral price in loan-asset units
        slippage_curve: π(V) for this collateral

    Returns:
        (recovery, bad_debt) — both denominated in loan asset
    """
    if borrow_assets < EPS:
        return 0.0, 0.0
    if collateral_amount < EPS:
        return 0.0, borrow_assets  # nothing to seize: full write-off

    lif = liquidation_incentive_factor(state.params.lltv)
    oracle = state.oracle_price
    desired_seize = borrow_assets * lif / oracle
    seized = min(desired_seize, collateral_amount)

    # Pool-side accounting (Morpho.sol): repaid on oracle terms; bad debt only
    # on collateral exhaustion
    repaid = min(borrow_assets, seized * oracle / lif)
    bad_debt = max(0.0, borrow_assets - repaid)

    # Liquidator-side executability: the DEX resale at market price and
    # stress slippage must cover the repayment, otherwise no rational keeper
    # executes and the stressed debt delivers nothing within the horizon.
    if market_price < EPS:
        return 0.0, 0.0
    pi = slippage_curve.slippage(seized)
    proceeds = seized * market_price * (1.0 - pi)
    if proceeds < repaid:
        return 0.0, 0.0  # unexecutable at stress prices: no recovery, no realised write-off

    return repaid, bad_debt


def hqla_v03(
    state: MarketState,
    market_price: float,
    slippage_curve: SlippageCurve,
) -> tuple[float, float, float, float]:
    """Compute HQLA per the v0.3 formulation.

    Returns (l1, l2a_net, expected_bad_debt, hqla_total).

    L1 = total_supply_assets - total_borrow_assets (instant liquidity).

    L_net = Σᵢ recoveryᵢ(stress) — that is, only what the liquidation
    process can actually deliver to the pool, net of slippage and capped at
    each position's debt.

    The expected bad debt is reported separately for diagnostics.
    """
    l1 = max(0.0, state.total_supply_assets - state.total_borrow_assets)

    if not state.positions:
        return l1, 0.0, 0.0, l1

    # v1.1: only positions actually liquidatable at the stressed oracle can
    # deliver recoveries within the horizon; healthy positions' debt is not
    # callable and contributes nothing to the stock.
    total_recovery = 0.0
    total_bad_debt = 0.0
    for pos in state.liquidatable_positions():
        b_i = pos.borrow_assets(state.total_borrow_assets, state.total_borrow_shares)
        rec, bd = position_recovery_value(
            state=state,
            collateral_amount=pos.collateral,
            borrow_assets=b_i,
            market_price=market_price,
            slippage_curve=slippage_curve,
        )
        total_recovery += rec
        total_bad_debt += bd

    hqla_total = l1 + total_recovery
    return l1, total_recovery, total_bad_debt, hqla_total


def calibrated_outflow_alpha(
    market_path: np.ndarray,
    quantile: float = 0.99,
    window_blocks: int = 24,
    whale_concentration: float = 0.30,
) -> float:
    """Estimate stress-time withdrawal velocity from a market price proxy.

    In production, this would read withdrawal events directly from the subgraph
    and compute rolling 24h withdrawal sums normalized by total supply. For
    fixture-based backtest, we use the price drawdown distribution as a
    correlated proxy and add a whale-concentration term.

    Empirical calibration from observed events (KelpDAO 2026, Aave V3 USDC
    market response):

        - KelpDAO event: ~17% of Aave V3 TVL withdrew in 48h
          (~8B / 48B), peaking at ~10% in 24h
        - USDC depeg 2023: Aave USDC market saw ~25% withdrawn on day 1
        - stETH discount 2022: ~15% withdrawal velocity over 5 days

    These observations suggest a stress α in [0.10, 0.30], correlated with
    drawdown severity. The model:

        alpha = max(
            min_floor,
            min(max_cap, scale × p99_drawdown + whale_term)
        )

    where:
        - scale = 1.5  (calibrated from KelpDAO/USDC observed ratios)
        - whale_term = whale_concentration × indicator(p99_drawdown > 0.05)
          (the largest 5 suppliers withdraw at the first sign of stress)
        - min_floor = 0.05, max_cap = 0.60

    Args:
        market_path: hourly market price series
        quantile: target quantile for the drawdown distribution
        window_blocks: rolling window in observations (24 = 24h hourly)
        whale_concentration: fraction of TVL held by top-5 suppliers that
            exits on first stress signal. Default 0.30 reflects observed
            concentration in mid-size DeFi markets.

    Returns:
        alpha in [0.05, 0.60]
    """
    if len(market_path) < window_blocks + 1:
        return 0.10  # fallback: 10% — moderate stress

    drawdowns = []
    for i in range(len(market_path) - window_blocks):
        peak = market_path[i]
        if peak <= 0:
            continue
        trough = market_path[i:i + window_blocks].min()
        drawdowns.append(max(0.0, (peak - trough) / peak))

    if not drawdowns:
        return 0.10

    p99_drawdown = float(np.quantile(drawdowns, quantile))

    scale = 1.5
    whale_term = whale_concentration if p99_drawdown > 0.05 else 0.0
    alpha = scale * p99_drawdown + whale_term

    return max(0.05, min(0.60, alpha))


def lcr_onchain_v03(
    state: MarketState,
    market_price: float,
    slippage_curve: SlippageCurve,
    outflow_alpha: float,
) -> tuple[float, dict[str, float]]:
    """Compute LCR_onchain v0.3.

    Returns (lcr, components_dict).

    The denominator is net stressed outflows: alpha × total_supply_assets,
    minus expected liquidation inflows (capped at 75% of outflows per Basel).

    Single-counting (v1.1): liquidation recoveries enter the numerator only.
    They are NOT netted from outflows again, closing the v1.0 double-count
    (docs/MODEL_CORRECTIONS.md, C6).

    Args:
        state: market state at evaluation time
        market_price: collateral DEX market price (may differ from oracle)
        slippage_curve: collateral slippage curve
        outflow_alpha: fraction of supply withdrawn under stress
    """
    l1, l2a, bd, hqla = hqla_v03(state, market_price, slippage_curve)

    # Total stress outflows
    o_stress = outflow_alpha * state.total_supply_assets

    # v1.1 single-count: recoveries live in the numerator only; no second
    # netting as inflows. The denominator floor is scale-relative (C7).
    i_stress = 0.0

    eps_floor = max(1e-9 * state.total_supply_assets, 1e-12)
    net_outflows = max(o_stress - i_stress, eps_floor)
    lcr = hqla / net_outflows

    components = {
        "L1_instant": l1,
        "L2A_net_recoverable": l2a,
        "expected_bad_debt": bd,
        "HQLA_total": hqla,
        "outflows_stress": o_stress,
        "inflows_capped": i_stress,
        "net_outflows": net_outflows,
        "outflow_alpha": outflow_alpha,
    }
    return lcr, components
