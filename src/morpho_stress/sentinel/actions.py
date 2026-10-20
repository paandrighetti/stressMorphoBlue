"""Advisory risk-reduction actions for vaults exposed to stressed Morpho Blue markets.

The rule is fixed in docs/SENTINEL.md. Inputs are one evaluation row per market (from
scripts/run_evaluation.py) and the vaults' allocations to those markets; the output is the list of
actions that the role allowed to reduce risk quickly could take: the sentinel of a Vault V2, or the
guardian, curator and allocator of a MetaMorpho (V1) vault. Nothing here signs a transaction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

TIERS = ("green", "yellow", "red")

ROLES = {
    ("v2", "revoke"): "sentinel: revoke",
    ("v2", "decrease_cap"): "sentinel: decreaseAbsoluteCap",
    ("v2", "deallocate"): "sentinel: deallocate",
    ("v1", "revoke"): "guardian: revokePendingCap",
    ("v1", "decrease_cap"): "curator: submitCap (a decrease applies at once)",
    ("v1", "deallocate"): "allocator: reallocate",
}


@dataclass(frozen=True)
class MarketReading:
    """One market's evaluation of the day. Amounts are in units of the loan asset."""

    market_id: str
    label: str
    tier: str
    alpha_star: float
    supply_assets: float
    utilization: float

    @property
    def absorbable_24h(self) -> float:
        """The largest outflow the market absorbs within 24 hours under the stress."""
        return self.alpha_star * self.supply_assets

    @property
    def idle_liquidity(self) -> float:
        """Supply not lent out now: what a withdrawal can take before any repayment."""
        return max(self.supply_assets * (1.0 - self.utilization), 0.0)


@dataclass(frozen=True)
class Allocation:
    """A vault's supply in one market. Amounts are in units of the loan asset; None if unknown."""

    vault: str
    vault_name: str
    version: str
    market_id: str
    supply_assets: float
    cap: float | None = None
    pending_cap: float | None = None


@dataclass(frozen=True)
class Action:
    vault: str
    vault_name: str
    version: str
    market_id: str
    label: str
    tier: str
    kind: str
    role: str
    amount: float | None
    coverage: float
    reason: str


def coverage(market: MarketReading, alloc: Allocation) -> float:
    """Absorbable 24-hour outflow over the vault's allocation; below 1 the vault cannot fully exit."""
    if alloc.supply_assets <= 0:
        return math.inf
    return market.absorbable_24h / alloc.supply_assets


def _action(market: MarketReading, alloc: Allocation, kind: str, amount: float | None,
            cov: float, reason: str) -> Action:
    return Action(
        vault=alloc.vault, vault_name=alloc.vault_name, version=alloc.version,
        market_id=market.market_id, label=market.label, tier=market.tier, kind=kind,
        role=ROLES[(alloc.version, kind)], amount=amount, coverage=cov, reason=reason,
    )


def actions_for(market: MarketReading, alloc: Allocation) -> list[Action]:
    """The actions of docs/SENTINEL.md section 2 for one vault in one market."""
    if market.tier not in TIERS:
        raise ValueError(f"unknown tier {market.tier!r} for {market.label}")
    if alloc.version not in ("v1", "v2"):
        raise ValueError(f"unknown vault version {alloc.version!r}")
    cov = coverage(market, alloc)
    pending_up = (alloc.pending_cap is not None and alloc.cap is not None
                  and alloc.pending_cap > alloc.cap)
    out: list[Action] = []
    if market.tier == "red":
        if pending_up:
            out.append(_action(market, alloc, "revoke", alloc.pending_cap, cov,
                               "red market: no cap increase"))
        if cov < 1.0:
            if alloc.cap is not None and alloc.cap > alloc.supply_assets:
                out.append(_action(market, alloc, "decrease_cap", alloc.supply_assets, cov,
                                   "red market and the vault could not exit within 24 hours: "
                                   "cap set to the current allocation"))
            amount = min(alloc.supply_assets, market.idle_liquidity)
            if amount > 0:
                out.append(_action(market, alloc, "deallocate", amount, cov,
                                   "red market and the vault could not exit within 24 hours: "
                                   "withdraw what the market's idle liquidity allows"))
    elif market.tier == "yellow" and pending_up and alloc.pending_cap > market.absorbable_24h:
        out.append(_action(market, alloc, "revoke", alloc.pending_cap, cov,
                           "yellow market: the pending cap exceeds what the market absorbs in 24 hours"))
    return out


def all_actions(markets: list[MarketReading], allocations: list[Allocation]) -> list[Action]:
    by_id = {m.market_id: m for m in markets}
    out: list[Action] = []
    for alloc in allocations:
        market = by_id.get(alloc.market_id)
        if market is not None:
            out.extend(actions_for(market, alloc))
    order = {"red": 0, "yellow": 1, "green": 2}
    return sorted(out, key=lambda a: (order[a.tier], a.coverage, a.vault_name, a.kind))
