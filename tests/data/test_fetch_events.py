"""Tests for the event fetcher's natural key (tx_hash, log_index).

Regression for the placeholder log_index = 0: every event of one type in a
transaction shared a key, which the dbt uniqueness tests caught on the real
cache (vault reallocations emit several Withdraw and Supply events per tx).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fetch_events.py"
_SPEC = importlib.util.spec_from_file_location("fetch_events", _SCRIPT)
fetch_events = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fetch_events)


def _raw(log_index: int | None, assets: str = "1000000") -> dict:
    raw = {
        "hash": "0x" + "ab" * 32,
        "logIndex": log_index,
        "timestamp": "1760000000",
        "blockNumber": "23500000",
        "type": "MarketWithdraw",
        "user": {"address": "0x" + "CD" * 20},
        "data": {"assets": assets, "shares": assets},
    }
    if log_index is None:
        del raw["logIndex"]
    return raw


def _row(log_index: int, assets: str = "1000000") -> dict:
    return fetch_events._normalize_event_row(
        "withdraw", _raw(log_index, assets), 6, 18, "0x" + "ee" * 32
    )


def test_log_index_comes_from_the_api():
    assert _row(7)["log_index"] == 7


def test_event_without_log_index_is_rejected():
    assert (
        fetch_events._normalize_event_row("withdraw", _raw(None), 6, 18, "0x" + "ee" * 32) is None
    )


def test_query_selects_log_index():
    assert "logIndex" in fetch_events.EVENTS_QUERY


def test_same_transaction_distinct_logs_are_all_kept():
    kept, dropped = fetch_events._dedupe_events([_row(3), _row(4), _row(5)])
    assert (len(kept), dropped) == (3, 0)


def test_repeated_log_from_pagination_is_dropped():
    kept, dropped = fetch_events._dedupe_events([_row(3), _row(3), _row(4)])
    assert (len(kept), dropped) == (2, 1)


def test_conflicting_payloads_for_one_log_fail_loudly():
    with pytest.raises(ValueError, match="conflicting payloads"):
        fetch_events._dedupe_events([_row(3, "1000000"), _row(3, "2000000")])
