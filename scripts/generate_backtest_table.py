"""Generate the backtest results table from the event fixtures.

Runs the three retained fixtures through the backtest engine and writes
docs/_generated/backtest_results.md. The published table is therefore produced
by the same code path a reader reproduces with notebooks/phase4_demo.py, never
transcribed by hand.

Usage:
    python scripts/generate_backtest_table.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from morpho_stress.backtest import (  # noqa: E402
    list_fixtures,
    load_event,
    run_backtest,
)
from morpho_stress.models.slippage import SlippageCurve  # noqa: E402

# Same curves as notebooks/phase4_demo.py. Kept in one place so the published
# table and the demonstration notebook cannot drift apart.
SLIPPAGE_CURVES = {
    "rsETH": SlippageCurve(asset_symbol="rsETH", a=5e-4, b=0.60, max_slippage=0.5),
    "USDC": SlippageCurve(asset_symbol="USDC", a=2e-5, b=0.45, max_slippage=0.3),
    "stETH": SlippageCurve(asset_symbol="stETH", a=3e-4, b=0.55, max_slippage=0.4),
}
FALLBACK = SlippageCurve(asset_symbol="fallback", a=3e-4, b=0.55, max_slippage=0.4)

# Display labels, ordered as in the report narrative.
LABELS = {
    "kelpdao_2026_04": "rsETH incident-inspired fixture (2026)",
    "usdc_depeg_2023_03": "USDC depeg (2023)",
    "steth_discount_2022_05": "Staked-Ether discount (2022)",
}
ORDER = ["kelpdao_2026_04", "usdc_depeg_2023_03", "steth_discount_2022_05"]


def _slippage_for(symbol: str) -> SlippageCurve:
    return SLIPPAGE_CURVES.get(symbol, FALLBACK)


def _fmt_ratio(x: float) -> str:
    if x != x:  # NaN
        return "n/a"
    if x == float("inf"):
        return "inf"
    return f"{x:.2f}"


def _fmt_hours(x: float) -> str:
    if x == float("inf"):
        return "infinite"
    return f"{x:.1f}h"


def _criterion(verdict, name: str):
    for c in verdict.criteria:
        if c.name == name:
            return c
    raise KeyError(f"criterion {name} not found in {verdict.event_id}")


def main() -> None:
    available = set(list_fixtures())
    missing = [e for e in ORDER if e not in available]
    if missing:
        sys.exit(f"generate_backtest_table FAILED: fixtures missing: {missing}")

    rows = []
    verdicts = []
    for event_id in ORDER:
        fixture = load_event(Path("data/fixtures") / event_id)
        collateral = fixture.meta.affected_collaterals[0]
        verdict = run_backtest(fixture, _slippage_for(collateral), n_mc_paths=200)
        verdicts.append(verdict)

        lcr = _criterion(verdict, "LCR_onchain_v03")
        tti = _criterion(verdict, "time_to_illiquid_24h")
        bd = _criterion(verdict, "P_bad_debt_gt_0")
        alpha = verdict.metrics.get("outflow_alpha_calibrated", float("nan"))

        rows.append(
            "| {label} | {lcr} ({lcr_sev}) | {alpha:.0%} | {tti} ({tti_sev}) | "
            "{bd:.0%} ({bd_sev}) | **{sev}** | **{pf}** |".format(
                label=LABELS[event_id],
                lcr=_fmt_ratio(lcr.value),
                lcr_sev=lcr.severity,
                alpha=alpha,
                tti=_fmt_hours(tti.value),
                tti_sev=tti.severity,
                bd=bd.value,
                bd_sev=bd.severity,
                sev=verdict.severity_flag,
                pf=verdict.pass_fail,
            )
        )

    n_pass = sum(1 for v in verdicts if v.pass_fail == "PASS")

    header = (
        "| Event | On-chain Liquidity Coverage Ratio | alpha | Time-to-illiquid "
        "| Probability bad debt > 0 | Severity | Verdict |\n"
        "|---|---|---|---|---|---|---|"
    )

    body = "\n".join(rows)
    footer = (
        f"\nAggregate: **{n_pass} of {len(ORDER)} events flagged** by the "
        "pre-specified criteria. Values are produced by "
        "`scripts/generate_backtest_table.py`, which runs the same engine and the "
        "same slippage curves as `notebooks/phase4_demo.py`. Severity labels are "
        "the engine's own, not editorial.\n"
    )

    out = Path("docs/_generated")
    out.mkdir(parents=True, exist_ok=True)
    (out / "backtest_results.md").write_text(
        header + "\n" + body + "\n" + footer, encoding="utf-8"
    )
    print("Wrote docs/_generated/backtest_results.md")
    print(header)
    print(body)


if __name__ == "__main__":
    main()
