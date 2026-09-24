"""Tests for the event fetcher's natural key (tx_hash, log_index) and pagination.

Regression for the placeholder log_index = 0: every event of one type in a
transaction shared a key, which the dbt uniqueness tests caught on the real
cache (vault reallocations emit several Withdraw and Supply events per tx).

Regression for skip pagination: a short page (999 of 1000) read as the end of
the data, so busy markets came back with no events at all.
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
        "txHash": "0x" + "ab" * 32,
        "logIndex": log_index,
        "timestamp": "1760000000",
        "blockNumber": "23500000",
        "type": "Withdraw",
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


def test_tx_hash_is_read_from_the_market_transactions_field():
    assert _row(7)["tx_hash"] == "0x" + "ab" * 32


def test_event_without_log_index_is_rejected():
    assert (
        fetch_events._normalize_event_row("withdraw", _raw(None), 6, 18, "0x" + "ee" * 32) is None
    )


def test_query_targets_market_transactions_with_log_index():
    query = fetch_events.EVENTS_QUERY
    assert "marketTransactions(" in query
    assert "logIndex" in query
    assert "  transactions(" not in query  # removed from the API in 2026


def test_query_filters_the_window_server_side_and_pages_with_the_cursor():
    query = fetch_events.EVENTS_QUERY
    assert "timestamp_gte: $timestampGte" in query
    assert "timestamp_lte: $timestampLte" in query
    assert "cursor: $cursor" in query
    assert "countTotal" in query
    assert "skip" not in query


def test_same_transaction_distinct_logs_are_all_kept():
    kept, dropped = fetch_events._dedupe_events([_row(3), _row(4), _row(5)])
    assert (len(kept), dropped) == (3, 0)


def test_repeated_log_from_pagination_is_dropped():
    kept, dropped = fetch_events._dedupe_events([_row(3), _row(3), _row(4)])
    assert (len(kept), dropped) == (2, 1)


def test_conflicting_payloads_for_one_log_fail_loudly():
    with pytest.raises(ValueError, match="conflicting payloads"):
        fetch_events._dedupe_events([_row(3, "1000000"), _row(3, "2000000")])


class _FakeClient:
    """Serves prepared pages; countTotal counts the events left after the cursor, as on the API."""

    def __init__(self, pages: list[list[dict]], count_total: int):
        self._pages = list(pages)
        self._left = count_total
        self.calls: list[dict] = []

    def _post(self, _query: str, variables: dict) -> dict:
        self.calls.append(dict(variables))
        items = self._pages.pop(0) if self._pages else []
        page = {"marketTransactions": {"pageInfo": {"countTotal": self._left}, "items": items}}
        self._left -= len(items)
        return page


def _fetch(client: _FakeClient) -> list[dict]:
    return fetch_events._fetch_event_type_for_market(
        client, "withdraw", "0x" + "ee" * 32, 1_750_000_000, 1_770_000_000, 6, 18
    )


def test_short_pages_do_not_end_the_fetch_only_an_empty_page_does():
    client = _FakeClient([[_raw(1), _raw(2)], [_raw(3)], []], count_total=3)
    assert [r["log_index"] for r in _fetch(client)] == [1, 2, 3]
    assert len(client.calls) == 3


def test_pages_are_chained_with_the_cursor_of_the_last_event_inside_the_window():
    client = _FakeClient([[_raw(1), _raw(2)], [_raw(3)], []], count_total=3)
    _fetch(client)
    first, second, third = client.calls
    assert first["cursor"] is None
    assert second["cursor"] == {"txHash": "0x" + "ab" * 32, "logIndex": 2}
    assert third["cursor"] == {"txHash": "0x" + "ab" * 32, "logIndex": 3}
    assert (first["timestampGte"], first["timestampLte"]) == (1_750_000_000, 1_770_000_000)


def test_fetch_fails_when_the_api_count_is_not_reached():
    client = _FakeClient([[_raw(1)], []], count_total=2)
    with pytest.raises(RuntimeError, match="1 events kept, API countTotal 2"):
        _fetch(client)
