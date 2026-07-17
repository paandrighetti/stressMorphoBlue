"""Interest Rate Model — AdaptiveCurveIRM (full adaptive version).

Float-arithmetic model of Morpho Blue's AdaptiveCurveIRM (v1.1, contract-faithful update scheme)
(`AdaptiveCurveIrm.sol`). Reference:

    Morpho Labs, *Morpho Blue Whitepaper* §5
    https://github.com/morpho-org/morpho-blue-irm

Two outputs at each block:

1. **Borrow rate ``r_b(U)``**: piecewise curve through ``rate_at_target`` at
   ``U = U_target``, with slope ratio ``curve_steepness`` between the two
   regimes (below / above target).

2. **Adaptive ``rate_at_target``**: evolves as a function of the deviation
   ``err = (U - U_target) / max(U_target, 1 - U_target)``, integrated over
   time:

       d(rate_at_target) / dt = rate_at_target × adjustment_speed × err

   Solved exactly over a block as ``rate_at_target × exp(speed × err × Δt)``,
   then clipped to ``[min_rate, max_rate]``.

The full adaptive layer matters for stress horizons of days–weeks, where the
rate-at-target can drift by tens of percent and feed back into borrower /
supplier behavior.

For unit consistency:
    - Rates are continuously compounded APR (annualized, base e).
    - Time deltas are in seconds; ``adjustment_speed`` is per-year.

All arithmetic is float64 native — we do not replicate the on-chain WAD math
exactly, since stress simulations do not need 1e-18 precision and the
computational savings are large.


REMAINING SIMPLIFICATIONS vs the mainnet contract (see docs/MODEL_CORRECTIONS.md):
* Exact exponentials (math.exp / expm1) instead of the contract's 3-term
  wTaylorCompounded approximation; float64 instead of WAD fixed-point.
* The fee recipient's supply shares are not tracked individually. Total
  supply accrues the FULL interest (as on-chain), so utilisation and the
  S - B liquidity margin match the contract; only the split of supply
  between fee recipient and other suppliers is aggregated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from morpho_stress.models.constants import EPS, SECONDS_PER_YEAR


@dataclass(frozen=True, slots=True)
class IrmParams:
    """AdaptiveCurveIRM parameters — see Morpho Labs `AdaptiveCurveIrm.sol`.

    Default values match the deployed mainnet IRM.
    """

    target_utilization: float = 0.9
    curve_steepness: float = 4.0  # k_d in the whitepaper
    adjustment_speed: float = 50.0  # per year, in 1e0 units
    initial_rate_at_target: float = 0.04  # 4% APR

    # Bounds (as in Morpho contract)
    min_rate_at_target: float = 0.001  # 0.1% APR
    max_rate_at_target: float = 2.0  # 200% APR


def borrow_rate(utilization: float, rate_at_target: float, params: IrmParams) -> float:
    """Compute the instantaneous borrow APR given current utilization.

    Piecewise curve:
        - U < U_target:
              rate = rate_at_target × (1 - (1 - U/U_target) / k_d)
        - U >= U_target:
              rate = rate_at_target × (1 + (U - U_target) / (1 - U_target) × (k_d - 1))

    The two branches meet at U = U_target with value rate_at_target.
    """
    u = max(0.0, min(1.0, utilization))
    u_t = params.target_utilization
    k = params.curve_steepness

    if u < u_t:
        ratio = (u_t - u) / max(u_t, EPS)
        coeff = 1.0 - ratio / k
    else:
        ratio = (u - u_t) / max(1.0 - u_t, EPS)
        coeff = 1.0 + ratio * (k - 1.0)

    return rate_at_target * coeff


def supply_rate(borrow_apr: float, utilization: float, fee: float) -> float:
    """Effective supplier APR: r_borrow × U × (1 - fee)."""
    return borrow_apr * max(0.0, utilization) * (1.0 - fee)


def update_rate_at_target(
    rate_at_target: float,
    utilization: float,
    params: IrmParams,
    elapsed_seconds: int,
) -> float:
    """Adaptive update of rate_at_target — Morpho's adaptive curve step.

    Mechanism: the deviation, normalised piecewise as in the contract,
        err = (U - U_target) / U_target            if U < U_target
        err = (U - U_target) / (1 - U_target)      if U >= U_target
    drives an exponential adjustment of rate_at_target:
        d(rate_at_target) / dt = rate_at_target × speed × err
    Closed-form solution over Δt:
        rate_at_target_new = rate_at_target × exp(speed × err × Δt / year)

    The result is clipped to ``[min_rate_at_target, max_rate_at_target]``.
    """
    if elapsed_seconds <= 0 or rate_at_target <= 0:
        return rate_at_target

    u = max(0.0, min(1.0, utilization))
    u_t = params.target_utilization
    norm = u_t if u < u_t else (1.0 - u_t)
    err = (u - u_t) / max(norm, EPS)

    exponent = params.adjustment_speed * err * elapsed_seconds / SECONDS_PER_YEAR
    # Clip exponent to avoid float overflow on extreme inputs
    exponent = max(-50.0, min(50.0, exponent))
    new_rate = rate_at_target * math.exp(exponent)

    return max(params.min_rate_at_target, min(params.max_rate_at_target, new_rate))


def accrue(
    total_supply_assets: float,
    total_borrow_assets: float,
    fee: float,
    rate_at_target: float,
    params: IrmParams,
    elapsed_seconds: int,
    *,
    update_target: bool = True,
) -> tuple[float, float, float]:
    """Accrue interest over ``elapsed_seconds`` and (optionally) update rate_at_target.

    Returns ``(new_supply_assets, new_borrow_assets, new_rate_at_target)``.

    Contract-faithful scheme: the utilisation error is normalised piecewise,
    rate_at_target evolves as start*exp(speed*err*dt), and interest accrues at
    the borrow rate evaluated at the AVERAGE rate-at-target over the interval,
    approximated as (start + end + 2*mid)/4 with mid = start*exp(la/2), exactly
    as AdaptiveCurveIrm.sol does. Total supply accrues the FULL interest (the
    fee is a split of supply, not a leak).

"""
    if elapsed_seconds <= 0 or total_supply_assets < EPS:
        return total_supply_assets, total_borrow_assets, rate_at_target

    u = total_borrow_assets / total_supply_assets if total_supply_assets > EPS else 0.0
    u_c = max(0.0, min(1.0, u))
    u_t = params.target_utilization
    norm = u_t if u_c < u_t else (1.0 - u_t)
    err = (u_c - u_t) / max(norm, EPS)

    if update_target:
        la = params.adjustment_speed * err * elapsed_seconds / SECONDS_PER_YEAR
        la = max(-50.0, min(50.0, la))
        clip = lambda r: max(params.min_rate_at_target,
                             min(params.max_rate_at_target, r))
        end_rat = clip(rate_at_target * math.exp(la))
        mid_rat = clip(rate_at_target * math.exp(la / 2.0))
        avg_rat = (rate_at_target + end_rat + 2.0 * mid_rat) / 4.0
    else:
        end_rat = rate_at_target
        avg_rat = rate_at_target

    r_b = borrow_rate(u, avg_rat, params)
    growth = math.expm1(r_b * elapsed_seconds / SECONDS_PER_YEAR)
    interest = total_borrow_assets * growth

    new_borrow = total_borrow_assets + interest
    new_supply = total_supply_assets + interest

    return new_supply, new_borrow, end_rat
