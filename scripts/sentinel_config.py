"""Write config.local.yaml for the daily sentinel run (docs/SENTINEL.md, section 3).

The window is the last --days days up to now, the roster is markets_top.yaml, the sampling cadences
are those of config.yaml (the published evaluation's), and the Morpho API serves the position book.
The Ethereum endpoint is Alchemy when the ALCHEMY_KEY environment variable is set (a repository
secret); otherwise the first public endpoints that answer a historical-state request at the window's
start (an archive read, which the state and oracle samplers need).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import click
import httpx
import yaml

PUBLIC_RPCS = (
    "https://eth.llamarpc.com",
    "https://ethereum-rpc.publicnode.com",
    "https://eth.drpc.org",
    "https://1rpc.io/eth",
    "https://eth-mainnet.public.blastapi.io",
    "https://cloudflare-eth.com",
)
MORPHO_API = "https://api.morpho.org/graphql"
BLOCKS_PER_DAY = 7200


def _rpc(url: str, method: str, params: list) -> object:
    r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                   timeout=15.0)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(str(body["error"])[:200])
    return body["result"]


def archive_ok(url: str, contract: str, days: int) -> bool:
    try:
        head = int(_rpc(url, "eth_blockNumber", []), 16)
        old = hex(head - (days + 1) * BLOCKS_PER_DAY)
        _rpc(url, "eth_getStorageAt", [contract, "0x0", old])
        return True
    except Exception as exc:  # noqa: BLE001 - a failing endpoint is skipped, not fatal
        click.echo(f"  {url}: {str(exc)[:120]}")
        return False


@click.command()
@click.option("--template", default="config.yaml")
@click.option("--roster", default="markets_top.yaml")
@click.option("--days", default=30, show_default=True)
@click.option("--out", default="config.local.yaml")
def main(template: str, roster: str, days: int, out: str) -> None:
    cfg = yaml.safe_load(Path(template).read_text(encoding="utf-8"))
    markets = yaml.safe_load(Path(roster).read_text(encoding="utf-8"))["markets"]
    contract = cfg["morpho_blue"]["contract"]
    key = os.environ.get("ALCHEMY_KEY", "").strip()
    if key:
        primary, label = "https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_KEY}", "Alchemy (repository secret)"
        fallback = next((u for u in PUBLIC_RPCS if archive_ok(u, contract, days)), None)
    else:
        click.echo("ALCHEMY_KEY not set: probing public endpoints for archive reads")
        working = [u for u in PUBLIC_RPCS if archive_ok(u, contract, days)]
        if not working:
            raise click.ClickException("no public endpoint serves archive reads; set ALCHEMY_KEY")
        primary, label = working[0], f"public endpoint {working[0]}"
        fallback = working[1] if len(working) > 1 else None
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    cfg["network"]["rpc_url"] = primary
    cfg["network"]["rpc_url_fallback"] = fallback
    cfg["subgraph"] = {"url": MORPHO_API, "api_key": None}
    cfg["range"] = {"start_ts": (end - timedelta(days=days)).isoformat(), "end_ts": end.isoformat()}
    cfg["markets"] = markets
    Path(out).write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    click.echo(f"rpc: {label}; fallback: {fallback}; window {cfg['range']['start_ts']} to "
               f"{cfg['range']['end_ts']}; {len(markets)} markets")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"rpc_label={label}\n")


if __name__ == "__main__":
    main()
