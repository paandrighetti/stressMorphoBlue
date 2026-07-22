"""Build immutable metadata for the committed evaluation outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical_sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--state-block", required=True, type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evaluation_manifest.json"),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        default=[
            Path("docs/evaluation_results.csv"),
            Path("docs/evaluation_summary.json"),
        ],
    )
    args = parser.parse_args()

    missing = [path for path in args.files if not path.is_file()]
    if missing:
        parser.error(f"missing evaluation outputs: {missing}")

    manifest = {
        "schema_version": 1,
        "snapshot_date": args.snapshot_date,
        "chain_id": 1,
        "network": "ethereum-mainnet",
        "state_block": args.state_block,
        "engine": "v1.1",
        "publication_policy": (
            "Snapshot metadata and hashes are immutable for the committed "
            "evaluation outputs. A new evaluation requires a new manifest."
        ),
        "files": {
            path.as_posix(): {
                "sha256": canonical_sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in args.files
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
