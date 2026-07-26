"""Generate the roster composition fragment for REPORT.md section 4.1.

Reads docs/evaluation_results.csv and writes docs/_generated/report_roster.md.

Units are reported separately. Markets whose loan asset is WETH are denominated
in WETH and are never added to USD-denominated supplies: no exchange rate is
assumed anywhere in this fragment. The previous hand-written section mixed the
two and quoted class totals that no committed artifact reproduces.

Usage:
    python scripts/generate_roster_table.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("docs/evaluation_results.csv")
OUT_PATH = Path("docs/_generated/report_roster.md")

# Collateral prefix -> asset class. First match wins, longest prefixes first.
CLASS_RULES = [
    ("PT-", "Pendle principal tokens"),
    ("cbBTC", "Wrapped Bitcoin"),
    ("WBTC", "Wrapped Bitcoin"),
    ("LBTC", "Wrapped Bitcoin"),
    ("wstETH", "Liquid staking tokens"),
    ("weETH", "Liquid staking tokens"),
]
DEFAULT_CLASS = "Yield-bearing and synthetic stables"

CLASS_ORDER = [
    "Wrapped Bitcoin",
    "Liquid staking tokens",
    "Yield-bearing and synthetic stables",
    "Pendle principal tokens",
]


def classify(market_label: str) -> str:
    collateral = market_label.split("/")[0]
    for prefix, klass in CLASS_RULES:
        if collateral.startswith(prefix):
            return klass
    return DEFAULT_CLASS


def loan_asset(market_label: str) -> str:
    return market_label.split("/")[-1]


def fmt_usd(value: float) -> str:
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value / 1e3:.0f}k"


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"{CSV_PATH} missing: run scripts/run_evaluation.py first")

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))

    usd = defaultdict(float)
    weth = defaultdict(float)
    counts = defaultdict(int)
    collaterals = defaultdict(set)

    for r in rows:
        klass = classify(r["market"])
        supply = float(r["supply_assets"])
        counts[klass] += 1
        collaterals[klass].add(r["market"].split("/")[0])
        if loan_asset(r["market"]) == "WETH":
            weth[klass] += supply
        else:
            usd[klass] += supply

    lines = [
        "The roster spans four collateral asset classes. Supplies are reported in "
        "the market's own loan asset: markets quoted in Wrapped Ether are listed "
        "separately and are not converted, so no exchange-rate assumption enters "
        "any figure below.",
        "",
        "| Asset class | Markets | Supply, USD-quoted loan assets | Supply, WETH-quoted loan assets | Collaterals |",
        "|---|---:|---:|---:|---|",
    ]

    for klass in CLASS_ORDER:
        if counts[klass] == 0:
            continue
        weth_cell = f"{weth[klass]:,.0f} WETH" if weth[klass] else "n/a"
        lines.append(
            f"| {klass} | {counts[klass]} | {fmt_usd(usd[klass])} | {weth_cell} | "
            f"{', '.join(sorted(collaterals[klass]))} |"
        )

    total_usd = sum(usd.values())
    total_weth = sum(weth.values())
    lines.append(
        f"| **Total, {len(rows)} evaluated markets** | **{len(rows)}** | "
        f"**{fmt_usd(total_usd)}** | **{total_weth:,.0f} WETH** | |"
    )

    lines += [
        "",
        "Loan assets across the roster are USDC, USDT, PYUSD, RLUSD, USDtb, AUSD "
        "and WETH. The two monitored markets excluded from evaluation are listed "
        "in the exclusions block of section 4.4 and contribute to none of the "
        "totals above.",
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
