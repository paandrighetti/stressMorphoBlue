"""The sentinel's rule (docs/SENTINEL.md section 2), its history and its report, offline."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from morpho_stress.sentinel.actions import Allocation, MarketReading, actions_for, all_actions
from morpho_stress.sentinel.report import (
    append_history,
    history_rows,
    previous_state,
    render,
)


def market(tier: str, alpha_star: float = 0.05, supply: float = 100.0, util: float = 0.95) -> MarketReading:
    return MarketReading("0xm", "cbBTC/USDC", tier, alpha_star, supply, util)


def alloc(supply: float, cap: float | None = None, pending: float | None = None,
          version: str = "v1") -> Allocation:
    return Allocation("0xvault", "Vault", version, "0xm", supply, cap, pending)


def kinds(actions):
    return [a.kind for a in actions]


def test_red_and_cannot_exit_freezes_cap_and_deallocates_idle_liquidity():
    m = market("red", alpha_star=0.05, supply=100.0, util=0.97)  # absorbable 5, idle 3
    acts = actions_for(m, alloc(supply=20.0, cap=50.0))
    assert kinds(acts) == ["decrease_cap", "deallocate"]
    assert acts[0].amount == 20.0
    assert acts[1].amount == pytest.approx(3.0)
    assert acts[0].coverage == pytest.approx(0.25)


def test_red_but_can_exit_only_revokes_a_pending_increase():
    m = market("red", alpha_star=0.08, supply=1_000.0)  # absorbable 80
    assert actions_for(m, alloc(supply=10.0, cap=50.0)) == []
    acts = actions_for(m, alloc(supply=10.0, cap=50.0, pending=200.0))
    assert kinds(acts) == ["revoke"]


def test_red_without_known_cap_still_deallocates():
    acts = actions_for(market("red", util=0.98), alloc(supply=20.0))
    assert kinds(acts) == ["deallocate"]
    assert acts[0].amount == pytest.approx(2.0)


def test_yellow_revokes_only_a_pending_cap_beyond_the_absorbable_outflow():
    m = market("yellow", alpha_star=0.2, supply=100.0)  # absorbable 20
    assert actions_for(m, alloc(supply=5.0, cap=10.0, pending=15.0)) == []
    assert kinds(actions_for(m, alloc(supply=5.0, cap=10.0, pending=25.0))) == ["revoke"]
    assert actions_for(m, alloc(supply=50.0, cap=60.0)) == []


def test_green_never_acts():
    assert actions_for(market("green", alpha_star=0.5), alloc(supply=500.0, cap=1e9, pending=2e9)) == []


def test_roles_follow_the_vault_version():
    m = market("red", util=0.97)
    v2 = actions_for(m, alloc(supply=20.0, cap=50.0, pending=80.0, version="v2"))
    assert [a.role for a in v2] == ["sentinel: revoke", "sentinel: decreaseAbsoluteCap",
                                    "sentinel: deallocate"]
    v1 = actions_for(m, alloc(supply=20.0, cap=50.0, pending=80.0, version="v1"))
    assert [a.role.split(":")[0] for a in v1] == ["guardian", "curator", "allocator"]


def test_empty_allocation_has_infinite_coverage_and_no_action():
    acts = actions_for(market("red"), alloc(supply=0.0, cap=10.0))
    assert acts == []


def test_unknown_tier_or_version_is_an_error():
    with pytest.raises(ValueError):
        actions_for(market("orange"), alloc(1.0))
    with pytest.raises(ValueError):
        actions_for(market("red"), alloc(1.0, version="v3"))


def test_all_actions_ignores_markets_outside_the_day_and_orders_red_first():
    red = MarketReading("0xa", "A/USDC", "red", 0.05, 100.0, 0.97)
    yellow = MarketReading("0xb", "B/USDC", "yellow", 0.2, 100.0, 0.8)
    allocs = [Allocation("0x1", "V1", "v1", "0xb", 5.0, 10.0, 50.0),
              Allocation("0x2", "V2", "v1", "0xa", 50.0, 80.0, None),
              Allocation("0x3", "V3", "v1", "0xz", 50.0, 80.0, None)]
    acts = all_actions([red, yellow], allocs)
    assert [a.tier for a in acts] == ["red", "red", "yellow"]


def test_previous_state_counts_consecutive_runs_in_the_last_tier():
    rows = []
    for d, t in (("2026-10-01", "green"), ("2026-10-02", "red"), ("2026-10-03", "red")):
        rows.append(history_rows(d, 1, [market(t)]))
    hist = pd.concat(rows, ignore_index=True)
    assert previous_state(hist, "2026-10-04") == {"0xm": ("red", 2)}
    assert previous_state(hist, "2026-10-03") == {"0xm": ("red", 1)}
    assert previous_state(None, "2026-10-03") == {}


def test_append_history_replaces_a_rerun_of_the_same_date():
    first = history_rows("2026-10-02", 1, [market("red")])
    second = history_rows("2026-10-02", 2, [market("yellow")])
    hist = append_history(append_history(None, first), second)
    assert hist["tier"].tolist() == ["yellow"]


def test_report_lists_markets_actions_and_inputs_without_em_dash():
    m = market("red", util=0.97)
    acts = actions_for(m, alloc(supply=20.0, cap=50.0))
    text = render("2026-10-20", 123, [m], {"0xm": ("yellow", 3)}, acts,
                  [("msY/USDC", "no oracle price series")], "MetaMorpho V1: 1 vaults", {"Engine": "x"})
    assert "| cbBTC/USDC |" in text and "| red | yellow | 1 |" in text
    assert "decrease cap" in text and "curator: submitCap" in text
    assert "msY/USDC" in text and "Evaluation block: 123" in text
    assert "—" not in text
    assert not math.isnan(acts[0].coverage)
