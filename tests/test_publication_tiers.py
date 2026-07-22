"""Consistency tests for the committed publication snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs" / "evaluation_results.csv"
SUMMARY = ROOT / "docs" / "evaluation_summary.json"


def expected_tier(alpha_star: float) -> str:
    if alpha_star < 0.10:
        return "red"
    if alpha_star < 0.30:
        return "yellow"
    return "green"


def test_published_tiers_depend_only_on_alpha_star() -> None:
    df = pd.read_csv(RESULTS)

    assert "tier" in df.columns
    expected = df["alpha_star"].map(expected_tier)

    assert df["tier"].tolist() == expected.tolist()
    assert df["severity"].tolist() == expected.tolist()


def test_summary_tier_counts_match_committed_results() -> None:
    df = pd.read_csv(RESULTS)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    expected_counts = {
        colour: int((df["tier"] == colour).sum())
        for colour in ("red", "yellow", "green")
    }

    assert summary["tiers"] == expected_counts
    assert sum(expected_counts.values()) == int(summary["markets_evaluated"])
