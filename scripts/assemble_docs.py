"""Splice the generated markdown fragments into the publication documents.

Replaces the content between the marker pairs
    <!-- BEGIN GENERATED: name -->  ...  <!-- END GENERATED: name -->
with the content of docs/_generated/{name}.md, for:

    docs/REPORT.md      <- report_results
    README.md           <- readme_block
    MIRROR_ARTICLE.md   <- mirror_findings

Idempotent: re-running after a new evaluation refreshes the figures in
place. Fails loudly if a marker or a fragment is missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TARGETS = [
    ("docs/REPORT.md", "report_results"),
    ("README.md", "readme_block"),
    ("MIRROR_ARTICLE.md", "mirror_findings"),
]


def main() -> None:
    errors = []
    for doc_path, name in TARGETS:
        doc = Path(doc_path)
        frag = Path("docs/_generated") / f"{name}.md"
        if not frag.exists():
            errors.append(f"{frag} missing: run scripts/generate_report_tables.py first")
            continue
        text = doc.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"(<!-- BEGIN GENERATED: {name} -->\n).*?(\n<!-- END GENERATED: {name} -->)",
            re.S,
        )
        if not pattern.search(text):
            errors.append(f"{doc_path}: marker pair for '{name}' not found")
            continue
        new = pattern.sub(lambda m: m.group(1) + frag.read_text(encoding="utf-8").strip() + m.group(2), text)
        doc.write_text(new, encoding="utf-8")
        print(f"{doc_path}: injected {frag} ({len(frag.read_text(encoding='utf-8'))} chars)")
    if errors:
        sys.exit("assemble_docs FAILED:\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    main()
