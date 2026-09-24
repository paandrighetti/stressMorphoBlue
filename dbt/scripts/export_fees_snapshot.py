"""Write docs/_generated/fees_snapshot.md from the dbt fees models.

Run it after `dbt build` on the real cache. It reads the DuckDB file dbt writes
(dbt/target/morpho_stress.duckdb) and the DefiLlama series committed in
docs/benchmarks/. docs/FEES.md explains the method; the figures live here and
none of them is typed by hand.

Amounts stay in each market's loan asset: USD-stable loans are printed in $ at
par, WETH loans in WETH, and the two are never added up.

Usage (from the repository root):
    python dbt/scripts/export_fees_snapshot.py
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[2]
BENCHMARK = REPO / "docs" / "benchmarks" / "defillama_morpho_blue_ethereum_daily_fees.csv"
# Same set as scripts/generate_report_tables.py.
STABLE_LOANS = {"USDC", "USDT", "PYUSD", "RLUSD", "USDtb", "AUSD", "DAI", "USDS", "USDe"}
MART = "main_marts.mart_protocol_fees_daily"
INTERVALS = "main_intermediate.int_morpho__interest_intervals"


def fmt(value: float, loan: str) -> str:
    """$ for USD-stable loans, the token symbol otherwise. Adding 0.0 turns -0 into 0."""
    if loan in STABLE_LOANS:
        return f"${round(value) + 0.0:,.0f}"
    return f"{round(value, 2) + 0.0:,.2f} {loan}"


def loan_order(loan: str) -> int:
    return 0 if loan in STABLE_LOANS else 1


def full_days(con: duckdb.DuckDBPyConnection) -> tuple[date, date, int, int]:
    """First and last UTC day on which every market is covered for 24 hours."""
    n_markets = con.execute(f"select count(distinct market_id) from {MART}").fetchone()[0]
    first, last, n_days = con.execute(
        f"""
        select min(day)::date, max(day)::date, count(*)
        from (
            select day
            from {MART}
            group by 1
            having min(day_coverage) = 1 and count(*) = {n_markets}
        ) as d
        """
    ).fetchone()
    if first is None:
        raise SystemExit("no UTC day is fully covered for every market: nothing to export")
    if (last - first).days + 1 != n_days:
        raise SystemExit(f"full days are not contiguous between {first} and {last}")
    return first, last, n_days, n_markets


def by_loan_asset(con, first: date, last: date) -> list[str]:
    rows = con.execute(
        f"""
        select
            loan_asset_symbol,
            count(distinct market_id),
            sum(fees_loan_units),
            sum(supply_side_fees_loan_units),
            sum(revenue_loan_units),
            sum(stuck_interest_loan_units),
            sum(n_liquidations),
            sum(liquidation_incentive_loan_units)
        from {MART}
        where day::date between ? and ?
        group by 1
        """,
        [first, last],
    ).fetchall()
    rows.sort(key=lambda r: (loan_order(r[0]), -r[2]))
    out = [
        "| Loan asset | Markets | Fees | Supply-side fees | Revenue | Stuck interest | Liquidations | Liquidation incentive |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for loan, n, fees, supply_side, revenue, stuck, n_liq, incentive in rows:
        out.append(
            f"| {loan} | {n} | {fmt(fees, loan)} | {fmt(supply_side, loan)} | {fmt(revenue, loan)} "
            f"| {fmt(stuck, loan)} | {n_liq} | {fmt(incentive, loan)} |"
        )
    return out


def by_market(con, first: date, last: date) -> list[str]:
    rows = con.execute(
        f"""
        select
            market_label,
            left(market_id, 10),
            loan_asset_symbol,
            sum(fees_loan_units),
            sum(stuck_interest_loan_units),
            sum(n_liquidations),
            sum(liquidation_incentive_loan_units)
        from {MART}
        where day::date between ? and ?
        group by 1, 2, 3
        """,
        [first, last],
    ).fetchall()
    rows.sort(key=lambda r: (loan_order(r[2]), r[2], -r[3], r[1]))
    out = [
        "| Market | Id | Fees | Stuck interest | Liquidations | Liquidation incentive |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for label, short_id, loan, fees, stuck, n_liq, incentive in rows:
        out.append(
            f"| {label} | `{short_id}` | {fmt(fees, loan)} | {fmt(stuck, loan)} | {n_liq} | {fmt(incentive, loan)} |"
        )
    return out


def reconciliation(con) -> list[str]:
    n, n_markets, start, end, max_gap, n_zero, n_stuck, max_fee, max_fee_shares = con.execute(
        f"""
        select
            count(*),
            count(distinct market_id),
            min(ts_start)::date,
            max(ts_end)::date,
            max(abs(interest - interest_supply_ledger)
                / greatest(abs(supply_assets_start), abs(supply_assets_end), 1)),
            count(*) filter (where interest = 0),
            count(*) filter (where is_stuck),
            max(greatest(fee_start, fee_end)),
            max(abs(fee_shares_value_end) / greatest(abs(supply_assets_end), 1))
        from {INTERVALS}
        where is_covered
        """
    ).fetchone()
    return [
        f"- Covered intervals between two state reads: {n:,} over {n_markets} markets, {start} to {end}.",
        f"- Largest gap between the borrow-ledger and the supply-ledger interest: {max_gap:.1e} of the market's supply.",
        f"- Intervals with no interest booked (no transaction triggered an accrual): {n_zero:,}.",
        f"- Highest market fee read from the contract: {max_fee:.4f}. "
        f"Largest value of fee shares minted in one interval: {max_fee_shares:.1e} of the market's supply.",
        f"- Stuck intervals (utilization at the threshold at both reads): {n_stuck:,}.",
    ]


def stuck_markets(con) -> list[str]:
    rows = con.execute(
        f"""
        select
            m.market_label,
            left(i.market_id, 10),
            m.loan_asset_symbol,
            count(*),
            min(i.ts_start)::date,
            max(i.ts_end)::date,
            sum(i.interest),
            -- Simple annual rate over the time the interest accrued (lastUpdate
            -- to lastUpdate), on the borrow at the start of each interval.
            sum(i.interest)
            / sum(i.borrow_assets_start * (i.accrued_to_unix - i.accrued_from_unix))
            * 365 * 86400
        from {INTERVALS} as i
        inner join (select distinct market_id, market_label, loan_asset_symbol from {MART}) as m
            on m.market_id = i.market_id
        where i.is_covered and i.is_stuck
        group by 1, 2, 3
        order by 7 desc
        """
    ).fetchall()
    return [
        f"- {label} (`{short_id}`): {n} stuck intervals from {start} to {end}, {fmt(interest, loan)} "
        f"of interest booked, a simple annual rate of {rate:.0%} on the borrow "
        "over the time it accrued."
        for label, short_id, loan, n, start, end, interest, rate in rows
    ]


def benchmark(con, first: date, last: date) -> list[str]:
    with BENCHMARK.open(encoding="utf-8", newline="") as fh:
        series = {date.fromisoformat(r["date"]): float(r["fees_usd"]) for r in csv.DictReader(fh)}
    days = [d for d in series if first <= d <= last]
    if len(days) != (last - first).days + 1:
        return [
            f"- DefiLlama series covers {len(days)} of the {(last - first).days + 1} days: no comparison."
        ]
    llama = sum(series[d] for d in days)
    stable = sorted(STABLE_LOANS)
    placeholders = ", ".join("?" for _ in stable)
    ours, stuck = con.execute(
        f"""
        select
            sum(fees_loan_units + liquidation_incentive_loan_units),
            sum(stuck_interest_loan_units)
        from {MART}
        where day::date between ? and ? and loan_asset_symbol in ({placeholders})
        """,
        [first, last, *stable],
    ).fetchone()
    lines = [
        f"- DefiLlama, Morpho Blue on Ethereum, same days: ${llama:,.0f} (interest plus "
        "liquidation bonus, on the markets its adapter counts: docs/FEES.md, section 5).",
        f"- This project, USD-stable loan markets of the roster, same definition: ${ours:,.0f}, "
        f"{ours / llama:.0%} of DefiLlama's total. WETH loan markets are left out of the comparison.",
    ]
    if stuck > llama:
        lines.append(
            f"- The stuck interest alone (${stuck:,.0f}) exceeds DefiLlama's total over the same "
            "days, so DefiLlama's series cannot include it in full."
        )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", type=Path, default=REPO / "dbt" / "target" / "morpho_stress.duckdb")
    parser.add_argument(
        "--out", type=Path, default=REPO / "docs" / "_generated" / "fees_snapshot.md"
    )
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    con.execute("set TimeZone = 'UTC'")
    first, last, n_days, n_markets = full_days(con)

    lines = [
        "<!-- Generated by dbt/scripts/export_fees_snapshot.py from the dbt fees models. Do not edit. -->",
        "",
        f"Window: {n_days} full UTC days, {first} to {last}, {n_markets} markets. "
        "Amounts in each market's loan asset; USD-stable loans in $ at par.",
        "",
        "### By loan asset",
        "",
        *by_loan_asset(con, first, last),
        "",
        "### By market",
        "",
        *by_market(con, first, last),
        "",
        "### Reconciliation",
        "",
        *reconciliation(con),
        "",
        "### Stuck markets",
        "",
        *(stuck_markets(con) or ["- None."]),
        "",
        "### Benchmark",
        "",
        *benchmark(con, first, last),
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, so Windows writes the same LF file as Linux.
    args.out.write_bytes("\n".join(lines).encode("utf-8"))
    print(f"{args.out}: {n_days} days, {n_markets} markets")


if __name__ == "__main__":
    main()
