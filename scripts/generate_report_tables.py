"""Generate the publication markdown fragments from the evaluation outputs.

Reads docs/evaluation_results.csv and docs/evaluation_summary.json (produced
by scripts/run_evaluation.py) and writes three fragments to docs/_generated/:

    report_results.md   - headline paragraph + base table + extreme table
                          + documented exclusions (for docs/REPORT.md)
    readme_block.md     - the short headline block (for README.md)
    mirror_findings.md  - the key-findings paragraphs (for MIRROR_ARTICLE.md)

No number in the published documents should ever be hand-transcribed: this
script is the only path from engine output to prose. Supplies are printed in
the LOAN asset's own unit (USD-stable loans as $, WETH loans as WETH), so
non-dollar markets are never mislabelled as dollars.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import pandas as pd

STABLE_LOANS = {"USDC", "USDT", "PYUSD", "RLUSD", "USDtb", "AUSD", "DAI", "USDS", "USDe"}


def _loan_sym(market_label: str) -> str:
    return market_label.split("/")[-1]


def _fmt_supply(value: float, loan: str) -> str:
    if loan in STABLE_LOANS:
        return f"${value/1e6:,.1f}M" if value >= 1e6 else f"${value/1e3:,.0f}k"
    return f"{value:,.0f} {loan}"


def _pct(x: float, digits: int = 1) -> str:
    return f"{x*100:.{digits}f}%"


@click.command()
@click.option("--results", default="docs/evaluation_results.csv")
@click.option("--summary", default="docs/evaluation_summary.json")
@click.option("--outdir", default="docs/_generated")
@click.option("--snapshot-date", default=None,
              help="human-readable snapshot date; defaults to today (UTC)")
def main(results: str, summary: str, outdir: str, snapshot_date: str | None) -> None:
    df = pd.read_csv(results).sort_values("alpha_star")
    from datetime import date
    snap_date = snapshot_date or date.today().isoformat()
    snap_block = int(df["block"].max())
    snap_line = f"**Snapshot**: {snap_date}, state block {snap_block:,}. "
    sm = json.loads(Path(summary).read_text())
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    n = int(sm["markets_evaluated"])
    excl = sm.get("markets_excluded", [])
    tiers = sm.get("tiers", {})
    illiq = int(sm.get("extreme_illiquidity_failures", 0))
    insolv = int(sm.get("extreme_insolvency_failures", 0))
    a_med, a_min = sm.get("alpha_star_median"), sm.get("alpha_star_min")

    tier_txt = ", ".join(f"{tiers.get(k, 0)} {k}" for k in ("red", "yellow", "green"))
    head = (
        snap_line +
        f"**{n} of 26 monitored markets evaluated** (engine v1.1; exclusions documented below). "
        f"Survival frontier alpha\\*: median {_pct(a_med)}, minimum {_pct(a_min)}. "
        f"Tiers on alpha\\*: {tier_txt}. Under the extreme scenario, "
        f"**{illiq} of {n} markets fail the liquidity leg while {insolv} fail the solvency leg**: "
        f"at target utilisation, 24-hour risk on Morpho Blue is a liability-liquidity question, "
        f"not an asset-solvency one.\n"
    )

    base_cols = "| Market | Supply | U | alpha (window) | alpha\\* | TTI | P(insolv) | Tier |\n|---|---|---|---|---|---|---|---|\n"
    base_rows = []
    for r in df.itertuples():
        loan = _loan_sym(r.market)
        tti = "inf" if r.tti_hours == float("inf") or pd.isna(r.tti_hours) else f"{r.tti_hours:.1f}h"
        base_rows.append(
            f"| {r.market} | {_fmt_supply(r.supply_assets, loan)} | {_pct(r.utilization, 0)} "
            f"| {_pct(r.alpha, 0)} | **{_pct(r.alpha_star)}** | {tti} "
            f"| {_pct(r.p_insolvency, 0)} | {r.severity} |"
        )

    ext_cols = "| Market | dd applied | LSR (alpha=35%) | Latent insolvency | Illiquidity leg | Solvency leg |\n|---|---|---|---|---|---|\n"
    ext_rows = []
    for r in df.itertuples():
        ext_rows.append(
            f"| {r.market} | {_pct(r.extreme_drawdown_used, 0)} | {r.lsr24_extreme:.2f} "
            f"| {r.insolvency_extreme_pct:.2f}% | {'FAIL' if r.extreme_illiq_fail else 'pass'} "
            f"| {'FAIL' if r.extreme_insolv_fail else 'pass'} |"
        )

    excl_txt = "\n".join(f"* **{e['market']}**: {e['reason']}" for e in excl) or "* none"

    report = (
        "### Results (engine v1.1)\n\n" + head +
        "\n#### Base 24h stress, sorted by survival frontier\n\n" +
        base_cols + "\n".join(base_rows) +
        "\n\nalpha\\* = stressed liquid stock / supply: the largest 24h outflow fraction the market absorbs "
        "(oracle at the window-worst price, recoveries from stress-liquidatable positions included, "
        "keeper executability enforced). Tier thresholds anchor to the framework's documented alpha "
        "calibration band: red < 10%, yellow < 30%, green >= 30%.\n" +
        "\n#### Extreme scenario (class-aware drawdown, 35% outflows)\n\n" +
        ext_cols + "\n".join(ext_rows) +
        "\n\nLatent insolvency = debt not covered by collateral on stressed oracle terms "
        "(Morpho.sol exhaustion condition), independent of keeper execution.\n" +
        "\n#### Documented exclusions\n\n" + excl_txt + "\n"
    )
    (out / "report_results.md").write_text(report, encoding="utf-8")

    readme = (
        snap_line +
        f"**Under LCR-inspired 24-hour stress (LSR-24; engine v1.1)**: {n} of 26 monitored markets "
        f"evaluated. Survival frontier alpha\\* (max absorbable 24h outflow): median {_pct(a_med)}, "
        f"minimum {_pct(a_min)}; tiers {tier_txt}. Extreme scenario: {illiq}/{n} fail on liquidity, "
        f"{insolv}/{n} on solvency. Full tables in docs/REPORT.md; corrections vs v1.0 in "
        f"docs/MODEL_CORRECTIONS.md.\n"
    )
    (out / "readme_block.md").write_text(readme, encoding="utf-8")

    worst = df.iloc[0]
    best = df.iloc[-1]
    mirror = (
        f"As of {snap_date} (state block {snap_block:,}), across {n} evaluated markets, the survival frontier, the largest 24-hour outflow a market "
        f"absorbs from instantaneous liquidity plus stress-liquidatable recoveries, ranges from "
        f"{_pct(sm['alpha_star_min'])} ({worst.market}) to {_pct(best.alpha_star)} ({best.market}), "
        f"median {_pct(a_med)}. The binding variable is utilisation, not collateral class.\n\n"
        f"The second axis is the mirror image: under a class-aware extreme scenario, "
        f"{illiq} of {n} markets fail on liquidity while {insolv} fail on solvency; latent insolvency "
        f"stays below {df.insolvency_extreme_pct.max():.1f}% of supply everywhere. Position books are "
        f"conservative; liabilities are not.\n\n"
        f"Versus v1.0: the earlier yellow/green tiering was an artefact of a structural double-count "
        f"(recoveries in both numerator and netted outflows, correction C6) compounded by "
        f"non-callable healthy debt counted as monetisable (C4). The v1.1 engine removes both and "
        f"reports what remains: a liquidity question that rate-driven replenishment, not modelled in "
        f"this version, answers in practice.\n"
    )
    (out / "mirror_findings.md").write_text(mirror, encoding="utf-8")

    print(f"Wrote {out}/report_results.md, readme_block.md, mirror_findings.md")
    print("\n" + "=" * 30 + " PASTE BACK " + "=" * 30 + "\n")
    print(report)
    print(readme)
    print(mirror)


if __name__ == "__main__":
    main()
