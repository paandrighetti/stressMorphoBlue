"""The day's sentinel report, from the evaluation of run_evaluation.py and the vaults' allocations.

Reads the evaluation CSV and summary JSON of the day's run, the history in --data-dir (a checkout of
the sentinel-data branch), and the vault allocations from the Morpho API. Writes in --data-dir:
latest.md, history.csv, and the day's evaluation, allocations and actions under dated names; and
the Telegram digest to --digest. Nothing is signed or sent on-chain.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import click
import pandas as pd
import yaml

from morpho_stress.sentinel.actions import all_actions
from morpho_stress.sentinel.report import (
    actions_frame,
    append_history,
    history_rows,
    previous_state,
    readings_from_evaluation,
    render,
)
from morpho_stress.sentinel.vaults import fetch_allocations

REPO = "https://github.com/paandrighetti/stressMorphoBlue"


@click.command()
@click.option("--evaluation", "eval_path", required=True)
@click.option("--summary", "summary_path", required=True)
@click.option("--data-dir", required=True)
@click.option("--roster", default="markets_top.yaml")
@click.option("--date", default=None, help="UTC date of the run (default: today)")
@click.option("--rpc-label", default="not recorded")
@click.option("--commit", default="not recorded")
@click.option("--digest", default="run/digest.txt")
def main(eval_path: str, summary_path: str, data_dir: str, roster: str, date: str | None,
         rpc_label: str, commit: str, digest: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    date = date or datetime.now(UTC).strftime("%Y-%m-%d")
    out = Path(data_dir)
    for sub in ("evaluation", "allocations", "actions"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    evaluation = pd.read_csv(eval_path)
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    readings = readings_from_evaluation(evaluation)
    block = int(evaluation["block"].max())
    not_evaluated = [(e.get("market", e.get("market_id", "?")), e.get("reason", ""))
                     for e in summary.get("markets_excluded") or []]
    roster_ids = set(yaml.safe_load(Path(roster).read_text(encoding="utf-8"))["markets"])

    hist_path = out / "history.csv"
    history = pd.read_csv(hist_path) if hist_path.exists() else None
    previous = previous_state(history, date)

    allocations, notes = fetch_allocations(roster_ids)
    actions = all_actions(readings, allocations)

    shutil.copyfile(eval_path, out / "evaluation" / f"{date}.csv")
    pd.DataFrame([asdict(a) for a in allocations]).to_csv(out / "allocations" / f"{date}.csv",
                                                          index=False)
    actions_frame(date, actions).to_csv(out / "actions" / f"{date}.csv", index=False)
    append_history(history, history_rows(date, block, readings)).to_csv(hist_path, index=False)
    inputs = {
        "Engine": f"stressMorphoBlue {summary.get('engine', '?')}, "
                  f"methodology {summary.get('methodology_revision', '?')}, commit {commit}",
        "Ethereum endpoint": rpc_label,
        "Position book and vaults": "Morpho API (https://api.morpho.org/graphql)",
    }
    text = render(date, block, readings, previous, actions, not_evaluated, "; ".join(notes), inputs)
    (out / "latest.md").write_text(text, encoding="utf-8")

    reds = [m.label for m in readings if m.tier == "red"]
    changes = [f"{m.label} {previous[m.market_id][0]} to {m.tier}" for m in readings
               if m.market_id in previous and previous[m.market_id][0] != m.tier]
    lines = [f"Morpho sentinel {date}: {len(readings)} markets, {len(reds)} red, "
             f"{len(actions)} actions for {len({a.vault for a in actions})} vaults."]
    if changes:
        lines.append("Tier changes: " + "; ".join(changes) + ".")
    lines.append(f"{REPO}/blob/sentinel-data/latest.md")
    Path(digest).parent.mkdir(parents=True, exist_ok=True)
    Path(digest).write_text("\n".join(lines) + "\n", encoding="utf-8")
    click.echo("\n".join(lines))
    click.echo("; ".join(notes))


if __name__ == "__main__":
    main()
