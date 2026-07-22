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


def test_summary_exclusion_reasons_are_precise() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    exclusions = summary["markets_excluded"]

    assert all("unusable quotes" not in item["reason"] for item in exclusions)

    susds = [item for item in exclusions if item["market"] == "sUSDS/USDT"]
    assert len(susds) == 1
    assert (
        susds[0]["reason"]
        == "no slippage curve "
        "(insufficient slippage observations: 7 usable, 8 required)"
    )

