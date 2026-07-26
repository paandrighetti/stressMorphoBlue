"""Build immutable metadata for the committed evaluation outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical_bytes(path: Path) -> bytes:
    """Return platform-independent bytes for text publication outputs."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def canonical_sha256(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


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
        "methodology_revision": "rolling-window-v2",
        "publication_policy": (
            "Snapshot metadata and hashes are immutable for the committed "
            "evaluation outputs. A new evaluation requires a new manifest."
        ),
        "source_data_scope": (
            "This manifest pins the committed evaluation CSV and JSON. Raw "
            "Parquet caches are gitignored; data/manifest.json records acquisition "
            "runs, but this release does not bind the evaluation outputs to exact "
            "input-cache hashes."
        ),
        "files": {
            path.as_posix(): {
                "sha256": canonical_sha256(path),
                "size_bytes": len(canonical_bytes(path)),
            }
            for path in args.files
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
