"""Regenerate the dbt seeds from the repository's source-of-truth files.

roster_markets.csv        <- markets_top.yaml
evaluation_exclusions.csv <- docs/evaluation_summary.json

Run from anywhere: `python dbt/scripts/sync_seeds.py`. CI runs it and fails
if the committed seeds differ from the regenerated ones, so the roster can
never drift from the file the Python engine reads.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SEEDS = REPO / "dbt" / "seeds"


def main() -> None:
    roster = yaml.safe_load((REPO / "markets_top.yaml").read_text(encoding="utf-8"))["markets"]
    with (SEEDS / "roster_markets.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["market_id", "roster_rank"])
        for rank, market_id in enumerate(roster, start=1):
            writer.writerow([market_id.lower(), rank])

    summary = json.loads((REPO / "docs" / "evaluation_summary.json").read_text(encoding="utf-8"))
    with (SEEDS / "evaluation_exclusions.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["market_id", "market", "reason"])
        for row in summary.get("markets_excluded", []):
            writer.writerow([row["market_id"].lower(), row["market"], row["reason"]])

    print(f"roster_markets.csv: {len(roster)} rows; "
          f"evaluation_exclusions.csv: {len(summary.get('markets_excluded', []))} rows")


if __name__ == "__main__":
    main()
