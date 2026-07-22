from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.run_evaluation import _rolling_drawdowns


def test_rolling_drawdowns_includes_final_window() -> None:
    prices = np.arange(1.0, 26.0)
    result = _rolling_drawdowns(prices, window=24)
    assert result.shape == (2,)


def test_committed_evaluation_outputs_agree() -> None:
    frame = pd.read_csv("docs/evaluation_results.csv")
    summary = json.loads(Path("docs/evaluation_summary.json").read_text())
    tier_column = "tier" if "tier" in frame.columns else "severity"
    observed = {
        str(key): int(value)
        for key, value in frame[tier_column].value_counts().to_dict().items()
    }
    expected = {str(key): int(value) for key, value in summary["tiers"].items()}
    assert observed == expected
    assert len(frame) == int(summary["markets_evaluated"])
