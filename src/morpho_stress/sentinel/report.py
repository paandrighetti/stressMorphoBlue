"""The sentinel's outputs: the history of tiers and the day's report.

history.csv holds one row per market and run (date, block, market, tier, alpha_star, supply,
utilization). The report compares the day with the previous run, counts the consecutive runs each
market has spent in its tier, and lists the actions of actions.py by vault.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import pandas as pd

from .actions import Action, MarketReading

HISTORY_COLUMNS = ["date", "block", "market_id", "market", "tier", "alpha_star",
                   "supply_assets", "utilization"]


def readings_from_evaluation(df: pd.DataFrame) -> list[MarketReading]:
    return [
        MarketReading(
            market_id=str(r["market_id"]), label=str(r["market"]), tier=str(r["tier"]),
            alpha_star=float(r["alpha_star"]), supply_assets=float(r["supply_assets"]),
            utilization=float(r["utilization"]),
        )
        for _, r in df.iterrows()
    ]


def history_rows(date: str, block: int, readings: Iterable[MarketReading]) -> pd.DataFrame:
    return pd.DataFrame(
        [[date, block, m.market_id, m.label, m.tier, m.alpha_star, m.supply_assets, m.utilization]
         for m in readings],
        columns=HISTORY_COLUMNS,
    )


def append_history(history: pd.DataFrame | None, today: pd.DataFrame) -> pd.DataFrame:
    """Add today's rows, replacing an earlier run of the same date."""
    if history is None or history.empty:
        return today.reset_index(drop=True)
    kept = history[history["date"] != today["date"].iloc[0]]
    return pd.concat([kept, today], ignore_index=True).sort_values(["date", "market"],
                                                                   ignore_index=True)


def previous_state(history: pd.DataFrame | None, date: str) -> dict[str, tuple[str, int]]:
    """For each market, its tier at the last run before `date` and how many runs in a row it held it."""
    if history is None or history.empty:
        return {}
    past = history[history["date"] < date]
    out: dict[str, tuple[str, int]] = {}
    for mid, g in past.groupby("market_id"):
        tiers = g.sort_values("date")["tier"].tolist()
        last = tiers[-1]
        streak = 0
        for t in reversed(tiers):
            if t != last:
                break
            streak += 1
        out[str(mid)] = (last, streak)
    return out


def _amount(x: float | None, unit: str) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if math.isinf(x):
        return "unlimited"
    for size, suffix in ((1e9, " bn"), (1e6, " m"), (1e3, " k")):
        if abs(x) >= size:
            return f"{x / size:.2f}{suffix} {unit}"
    return f"{x:.2f} {unit}"


def _loan_unit(label: str) -> str:
    return label.split("/")[-1] if "/" in label else ""


def render(date: str, block: int, readings: list[MarketReading],
           previous: dict[str, tuple[str, int]], actions: list[Action],
           not_evaluated: list[tuple[str, str]], vault_note: str, inputs: dict[str, str]) -> str:
    counts = {t: sum(m.tier == t for m in readings) for t in ("red", "yellow", "green")}
    changes = [(m, previous[m.market_id][0]) for m in readings
               if m.market_id in previous and previous[m.market_id][0] != m.tier]
    order = {"red": 0, "yellow": 1, "green": 2}
    lines = [
        f"# Morpho Blue liquidity sentinel, {date}",
        "",
        "Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live "
        "data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) "
        "lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator "
        "(MetaMorpho) could take. No transaction is signed. Not investment advice.",
        "",
        "## Summary",
        "",
        f"- Markets evaluated: {len(readings)} (red {counts['red']}, yellow {counts['yellow']}, "
        f"green {counts['green']}); not evaluated: {len(not_evaluated)}.",
        f"- Tier changes since the previous run: {len(changes)}.",
        f"- Actions listed: {len(actions)}, for {len({a.vault for a in actions})} vaults.",
        f"- Vault data: {vault_note}",
        "",
        "## Markets",
        "",
        "alpha* is the largest share of supply the market can pay out within 24 hours under the "
        "stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.",
        "",
        "| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in sorted(readings, key=lambda m: (order[m.tier], m.alpha_star)):
        unit = _loan_unit(m.label)
        prev = previous.get(m.market_id)
        prev_tier = prev[0] if prev else "none"
        streak = prev[1] + 1 if prev and prev[0] == m.tier else 1
        lines.append(
            f"| {m.label} | {_amount(m.supply_assets, unit)} | {m.utilization:.1%} | "
            f"{m.alpha_star:.1%} | {_amount(m.absorbable_24h, unit)} | {m.tier} | {prev_tier} | {streak} |"
        )
    lines += ["", "## Actions by vault", ""]
    if actions:
        lines += [
            "Coverage is the market's absorbable outflow over the vault's allocation: below 1, the "
            "vault could not withdraw all of it within 24 hours even if it were first in line.",
            "",
            "| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for a in actions:
            unit = _loan_unit(a.label)
            cov = "n/a" if math.isinf(a.coverage) else f"{a.coverage:.2f}"
            lines.append(
                f"| {a.vault_name} (`{a.vault[:10]}`) | {a.version} | {a.label} | {a.tier} | {cov} | "
                f"{a.kind.replace('_', ' ')} | {a.role} | {_amount(a.amount, unit)} | {a.reason} |"
            )
    else:
        lines.append("None today.")
    if not_evaluated:
        lines += ["", "## Not evaluated today", "", "| Market | Reason |", "|---|---|"]
        lines += [f"| {label} | {reason} |" for label, reason in not_evaluated]
    lines += ["", "## Inputs", ""]
    lines += [f"- {k}: {v}" for k, v in inputs.items()]
    lines.append(f"- Evaluation block: {block}")
    return "\n".join(lines) + "\n"


def actions_frame(date: str, actions: list[Action]) -> pd.DataFrame:
    cols = ["date", "vault", "vault_name", "version", "market_id", "market", "tier", "action",
            "role", "amount", "coverage", "reason"]
    return pd.DataFrame(
        [[date, a.vault, a.vault_name, a.version, a.market_id, a.label, a.tier, a.kind, a.role,
          a.amount, a.coverage, a.reason] for a in actions],
        columns=cols,
    )
