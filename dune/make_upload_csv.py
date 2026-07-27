"""Generate the Dune upload artifact from the committed evaluation outputs.

Reads docs/evaluation_results.csv, lowercases market_id as a safeguard (Dune's
upload path mishandles mixed-case hex identifiers), and writes
dune/upload_eval_2026_07_16.csv. That file is the exact artifact uploaded as
the Dune dataset morpho_stress_eval_2026_07_16, so the dashboard table and the
manifest-pinned evaluation outputs cannot diverge.

Run from the repository root:

    python dune/make_upload_csv.py

Regenerate and re-upload only after a deliberate new evaluation run, and
rename both the file and the Dune dataset with the new snapshot date. Never
overwrite a dated dataset in place.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SRC = Path("docs/evaluation_results.csv")
DST = Path("dune/upload_eval_2026_07_16.csv")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"{SRC} missing: run from the repository root")
    rows = list(csv.reader(SRC.open(newline="", encoding="utf-8")))
    header, body = rows[0], rows[1:]
    if header[0] != "market_id":
        sys.exit("unexpected layout: first column is not market_id")
    out = [header] + [[r[0].lower()] + r[1:] for r in body]
    DST.parent.mkdir(exist_ok=True)
    with DST.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out)
    print(f"Wrote {DST}: {len(body)} data rows, {len(header)} columns")


if __name__ == "__main__":
    main()
