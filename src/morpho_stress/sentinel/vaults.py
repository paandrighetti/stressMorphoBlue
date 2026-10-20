"""Vault allocations to the roster's markets, from the Morpho API (keyless GraphQL).

The API's schema has changed before (see scripts/fetch_positions_api.py), so the queries are
assembled from introspection: only the fields the live schema exposes are requested, and a field
that is missing leaves the corresponding amount unknown instead of failing the run. MetaMorpho (V1)
vaults are read from `vaults`; Vault V2 from `vaultV2s` when the schema exposes per-market caps.
"""

from __future__ import annotations

import logging
from typing import Any

from morpho_stress.data.subgraph import SubgraphClient

from .actions import Allocation

log = logging.getLogger(__name__)

API_URL = "https://api.morpho.org/graphql"
PAGE = 500

_TREF = "type { name kind ofType { name kind ofType { name kind ofType { name kind } } } }"
_TYPE = ("query T($name: String!) { __type(name: $name) { name fields { name args { name " + _TREF
         + " } " + _TREF + " } inputFields { name } } }")


def _unwrap(tref: dict[str, Any] | None) -> str | None:
    while tref and not tref.get("name"):
        tref = tref.get("ofType")
    return tref.get("name") if tref else None


class Schema:
    def __init__(self, client: SubgraphClient) -> None:
        self._client = client
        self._cache: dict[str, dict[str, Any]] = {}

    def fields(self, type_name: str | None) -> dict[str, dict[str, Any]]:
        if not type_name:
            return {}
        if type_name not in self._cache:
            t = self._client._post(_TYPE, {"name": type_name}).get("__type") or {}
            self._cache[type_name] = t
        t = self._cache[type_name]
        out = {f["name"]: f for f in (t.get("fields") or [])}
        out.update({f["name"]: f for f in (t.get("inputFields") or [])})
        return out

    def field_type(self, type_name: str, field: str) -> str | None:
        f = self.fields(type_name).get(field)
        return _unwrap(f["type"]) if f else None

    def arg_type(self, type_name: str, field: str, arg: str) -> str | None:
        f = self.fields(type_name).get(field) or {}
        a = next((a for a in f.get("args") or [] if a["name"] == arg), None)
        return _unwrap(a["type"]) if a else None


def _raw(x: Any, decimals: int) -> float | None:
    if x is None:
        return None
    return float(x) / 10**decimals


def _paginate(client: SubgraphClient, query: str, root: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    skip = 0
    while True:
        data = client._post(query, {"first": PAGE, "skip": skip})
        items = ((data.get(root) or {}).get("items")) or []
        out.extend(items)
        if len(items) < PAGE:
            return out
        skip += PAGE


def _v1(client: SubgraphClient, schema: Schema, roster: set[str]) -> tuple[list[Allocation], str]:
    vault_t = schema.field_type("Query", "vaults")
    if vault_t is None:
        return [], "MetaMorpho V1 not exposed by the API"
    item_t = schema.field_type(vault_t, "items")
    state_t = schema.field_type(item_t or "", "state")
    alloc_t = schema.field_type(state_t or "", "allocation")
    alloc_fields = schema.fields(alloc_t)
    if "market" not in alloc_fields or "supplyAssets" not in alloc_fields:
        return [], f"MetaMorpho V1 allocation fields not found ({sorted(alloc_fields)})"
    picks = [f for f in ("supplyAssets", "supplyCap", "pendingSupplyCap") if f in alloc_fields]
    where_t = schema.arg_type("Query", "vaults", "where")
    where = "where: { chainId_in: [1] }" if "chainId_in" in schema.fields(where_t) else ""
    query = (
        "query V($first: Int!, $skip: Int!) { vaults(first: $first, skip: $skip"
        + (f", {where}" if where else "") + ") { items { address name asset { decimals } "
        "state { allocation { market { uniqueKey } " + " ".join(picks) + " } } } } }"
    )
    rows = _paginate(client, query, "vaults")
    out: list[Allocation] = []
    for v in rows:
        dec = int((v.get("asset") or {}).get("decimals") or 18)
        for a in ((v.get("state") or {}).get("allocation") or []):
            mid = ((a.get("market") or {}).get("uniqueKey") or "").lower()
            if mid not in roster:
                continue
            supply = _raw(a.get("supplyAssets"), dec) or 0.0
            cap = _raw(a.get("supplyCap"), dec)
            pending = _raw(a.get("pendingSupplyCap"), dec)
            if supply <= 0 and not cap:
                continue
            out.append(Allocation(vault=str(v["address"]).lower(), vault_name=str(v.get("name") or ""),
                                  version="v1", market_id=mid, supply_assets=supply, cap=cap,
                                  pending_cap=pending if pending else None))
    note = (f"MetaMorpho V1: {len({a.vault for a in out})} vaults allocated to the roster "
            f"(fields {', '.join(picks)})")
    return out, note


def _v2(_client: SubgraphClient, schema: Schema, _roster: set[str]) -> tuple[list[Allocation], str]:
    root_t = schema.field_type("Query", "vaultV2s")
    if root_t is None:
        return [], "Vault V2 not exposed by the API"
    item_t = schema.field_type(root_t, "items")
    fields = schema.fields(item_t)
    return [], f"Vault V2 not covered yet (fields of {item_t}: {', '.join(sorted(fields))})"


def fetch_allocations(roster: set[str], url: str = API_URL) -> tuple[list[Allocation], list[str]]:
    """Allocations of all vaults to the roster's markets, and a note per vault family."""
    roster = {m.lower() for m in roster}
    notes: list[str] = []
    out: list[Allocation] = []
    with SubgraphClient(url) as client:
        schema = Schema(client)
        for family in (_v1, _v2):
            try:
                allocs, note = family(client, schema, roster)
            except Exception as exc:  # noqa: BLE001 - a family that fails is reported, not fatal
                allocs, note = [], f"{family.__name__.strip('_')} failed: {exc}"
                log.warning(note)
            out.extend(allocs)
            notes.append(note)
    return out, notes
