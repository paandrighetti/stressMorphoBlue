"""scripts/fetch_metamorpho_vaults.py.

Fetch MetaMorpho vault state and allocation breakdown, then quantify
the gap between observed allocation and a framework-suggested optimal
allocation. This is the MVP delivery of the Hypothesis 2 of the
methodology: a quantitative measure of curator risk discipline.

Methodology:
    1. Fetch the top N MetaMorpho vaults by Total Value Locked from
       the Morpho API.
    2. For each vault, extract its current allocation across markets,
       expressed as the share of TVL deployed into each market.
    3. Cross-reference each market's risk tier (red/yellow/green-watch/
       green-strong) from the framework's panorama output.
    4. Compute the vault's curator risk score as the TVL-weighted
       severity of its allocations:
           score = sum_market (allocation_share * tier_weight)
       where tier_weight is mapped from severity: red=4, yellow=2,
       green-watch=1, green-strong=0.
    5. Vault risk hierarchy: vaults with score = 0 are perfectly
       conservative; vaults with score > 1 carry meaningful tier risk;
       vaults with score > 2 carry substantial tier risk.

Limitations:
    - Tier classifications come from our framework, not Morpho's official
      risk classification. A vault may legitimately allocate to a 'red'
      market if it priced in the risk explicitly.
    - Allocation snapshots are point-in-time; vault rebalancing dynamics
      are not captured.
    - We do not normalise by yield: a vault accepting more risk for
      higher yield is not penalised in this score, only flagged for
      review.

Usage:
    python scripts/fetch_metamorpho_vaults.py --top 20
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click
import httpx
import pandas as pd

logger = logging.getLogger(__name__)


VAULTS_QUERY = """
query GetTopVaults($first: Int!) {
  vaults(
    first: $first,
    orderBy: TotalAssetsUsd,
    orderDirection: Desc,
    where: { chainId_in: [1] }
  ) {
    items {
      address
      symbol
      name
      asset {
        symbol
        decimals
      }
      state {
        totalAssetsUsd
        totalAssets
        apy
        netApy
        allocation {
          supplyCap
          supplyAssets
          supplyAssetsUsd
          market {
            uniqueKey
            lltv
            collateralAsset { symbol }
            loanAsset { symbol }
          }
        }
      }
    }
  }
}
"""


# Tier weights for curator risk score
TIER_WEIGHTS = {
    "red": 4.0,
    "yellow": 2.0,
    "green-watch": 1.0,
    "green-strong": 0.0,
}


def fetch_vaults(top_n: int) -> list[dict]:
    """Fetch the top N MetaMorpho vaults from the Morpho API."""
    resp = httpx.post(
        "https://api.morpho.org/graphql",
        json={"query": VAULTS_QUERY, "variables": {"first": top_n}},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]["vaults"]["items"]


def load_market_tiers(profiles_path: Path, results_path: Path | None) -> dict[str, str]:
    """Build a market_id -> tier mapping.

    `profiles_path` is the JSON output of `enrich_forward_looking.py`
    (without --evaluate). It contains the per-market profile but not the
    tier. The tier is computed by re-running the assess_all_markets
    function on the loaded profiles.

    For the MVP, we re-run the assessment to get the tier mapping.
    """
    if not profiles_path.exists():
        raise FileNotFoundError(
            f"market_profiles.json not found at {profiles_path}; "
            "run scripts/enrich_forward_looking.py first"
        )
    with profiles_path.open() as f:
        profiles_data = json.load(f)

    # We need to rerun the assessment, which requires building MarketProfile
    # objects. Import here to avoid a hard dependency if user wants only
    # to fetch raw vault data.
    from morpho_stress.backtest.forward_looking import (
        MarketProfile,
        assess_all_markets,
    )

    profiles = [MarketProfile(**p) for p in profiles_data]
    results = assess_all_markets(profiles, n_mc_paths=100)

    # Map by market_label and by market_id reverse-lookup
    tier_by_label = {r.market_label: getattr(r, "severity_tier", r.severity_flag) for r in results}

    return tier_by_label


def label_for_market(coll: str, loan: str, lltv_wei: str | int) -> str:
    """Match the label format used in the panorama: 'COLL/LOAN (LLTV=X.XX%)'."""
    lltv_pct = float(lltv_wei) / 1e18 * 100
    return f"{coll}/{loan} (LLTV={lltv_pct:.2f}%)"


def compute_curator_score(
    allocations: list[dict], tier_by_label: dict[str, str]
) -> tuple[float, dict[str, float]]:
    """Compute the curator's TVL-weighted tier-severity score.

    Returns (score, breakdown) where breakdown is a dict mapping each
    tier to its share of the vault's TVL.
    """
    total_tvl = sum(float(a["supplyAssetsUsd"] or 0) for a in allocations)
    if total_tvl <= 0:
        return 0.0, {}

    breakdown = {"red": 0.0, "yellow": 0.0, "green-watch": 0.0, "green-strong": 0.0, "unknown": 0.0}
    score = 0.0
    for a in allocations:
        usd = float(a["supplyAssetsUsd"] or 0)
        if usd <= 0:
            continue
        market = a.get("market")
        if market is None:
            # Idle or deprecated market entry; bucket as unknown
            breakdown["unknown"] = breakdown.get("unknown", 0.0) + usd / total_tvl
            continue
        coll_obj = market.get("collateralAsset")
        loan_obj = market.get("loanAsset")
        lltv = market.get("lltv")
        if coll_obj is None or loan_obj is None or lltv is None:
            # Idle market (collateralAsset null is the Morpho convention for
            # the "idle" pseudo-market used for queueing assets without
            # active deployment). Bucket as unknown.
            breakdown["unknown"] = breakdown.get("unknown", 0.0) + usd / total_tvl
            continue
        coll = coll_obj.get("symbol")
        loan = loan_obj.get("symbol")
        if coll is None or loan is None:
            breakdown["unknown"] = breakdown.get("unknown", 0.0) + usd / total_tvl
            continue
        label = label_for_market(coll, loan, lltv)
        tier = tier_by_label.get(label, "unknown")
        share = usd / total_tvl
        breakdown[tier] = breakdown.get(tier, 0.0) + share
        if tier in TIER_WEIGHTS:
            score += share * TIER_WEIGHTS[tier]

    return score, breakdown


def render_vault_report(
    vaults: list[dict], tier_by_label: dict[str, str]
) -> pd.DataFrame:
    """Build a DataFrame of vault scores ready for sorting and printing."""
    rows = []
    for v in vaults:
        state = v.get("state") or {}
        allocations = state.get("allocation") or []
        tvl_usd = float(state.get("totalAssetsUsd") or 0)
        if tvl_usd <= 0:
            continue
        score, breakdown = compute_curator_score(allocations, tier_by_label)
        rows.append({
            "vault_name": v["name"],
            "vault_symbol": v["symbol"],
            "vault_address": v["address"],
            "asset": v["asset"]["symbol"],
            "tvl_usd": tvl_usd,
            "n_allocations": len(allocations),
            "curator_score": score,
            "share_red": breakdown.get("red", 0.0),
            "share_yellow": breakdown.get("yellow", 0.0),
            "share_green_watch": breakdown.get("green-watch", 0.0),
            "share_green_strong": breakdown.get("green-strong", 0.0),
            "share_unknown": breakdown.get("unknown", 0.0),
        })
    return pd.DataFrame(rows).sort_values("tvl_usd", ascending=False)


@click.command()
@click.option("--top", "top_n", default=20, type=int, help="Top N vaults by TVL")
@click.option(
    "--profiles-path",
    default="data/cache/market_profiles.json",
    type=click.Path(),
    help="Path to market_profiles.json (output of enrich_forward_looking.py)",
)
@click.option(
    "--output",
    default="data/cache/metamorpho_vaults.csv",
    type=click.Path(),
)
def main(top_n: int, profiles_path: str, output: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logger.info("Loading market tiers from %s", profiles_path)
    tier_by_label = load_market_tiers(Path(profiles_path), None)
    logger.info("Loaded tiers for %d markets", len(tier_by_label))

    logger.info("Fetching top %d MetaMorpho vaults from Morpho API...", top_n)
    vaults = fetch_vaults(top_n)
    logger.info("Fetched %d vaults", len(vaults))

    df = render_vault_report(vaults, tier_by_label)
    df.to_csv(output, index=False)
    logger.info("Wrote %d vault rows to %s", len(df), output)

    # Pretty-print the panorama
    print()
    print("=" * 110)
    print("METAMORPHO VAULT CURATOR DISCIPLINE — RANKED BY TVL")
    print("=" * 110)
    print(
        f"{'vault (asset)':<38} {'TVL ($M)':>10} {'#alloc':>7} "
        f"{'score':>6} {'red%':>6} {'yel%':>6} {'gw%':>6} {'gs%':>6} {'unk%':>6}"
    )
    print("-" * 110)
    for _, r in df.iterrows():
        label = f"{r['vault_name'][:30]} ({r['asset']})"
        print(
            f"{label:<38} {r['tvl_usd']/1e6:>10.1f} {r['n_allocations']:>7d} "
            f"{r['curator_score']:>6.2f} {r['share_red']*100:>5.1f}% "
            f"{r['share_yellow']*100:>5.1f}% {r['share_green_watch']*100:>5.1f}% "
            f"{r['share_green_strong']*100:>5.1f}% {r['share_unknown']*100:>5.1f}%"
        )

    print()
    print("Reading the score:")
    print("  0.0      = perfectly conservative (100% in green-strong)")
    print("  ~1.0     = mostly green-watch / some yellow")
    print("  ~2.0     = significant yellow exposure")
    print("  > 2.0    = substantial red/yellow exposure (curator review warranted)")


if __name__ == "__main__":
    main()
