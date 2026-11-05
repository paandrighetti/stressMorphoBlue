# Morpho Blue liquidity sentinel, 2026-11-05

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 5, yellow 18, green 1); not evaluated: 2.
- Tier changes since the previous run: 8.
- Actions listed: 6, for 4 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| AA_FalconXUSDC/USDC | 7.66 m USDC | 90.2% | 9.8% | 747.54 k USDC | red | red | 3 |
| weETH/PYUSD | 14.52 m PYUSD | 90.2% | 9.8% | 1.42 m PYUSD | red | yellow | 1 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 7 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.0% | 10.0% | 168.06 k PYUSD | red | red | 16 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 13 |
| sUSDe/PYUSD | 115.03 m PYUSD | 89.6% | 10.4% | 11.92 m PYUSD | yellow | red | 1 |
| sUSDe/USDtb | 892.24 k USDtb | 89.6% | 10.4% | 92.96 k USDtb | yellow | yellow | 5 |
| cbBTC/USDC | 336.23 m USDC | 89.5% | 10.5% | 35.17 m USDC | yellow | red | 1 |
| wstETH/USDC | 36.96 m USDC | 89.4% | 10.6% | 3.91 m USDC | yellow | red | 1 |
| WBTC/USDC | 137.61 m USDC | 89.2% | 10.8% | 14.87 m USDC | yellow | red | 1 |
| PT-apyUSD-18JUN2026/USDC | 3.73 m USDC | 88.8% | 11.2% | 415.39 k USDC | yellow | red | 1 |
| wstETH/WETH | 8.67 k WETH | 87.7% | 12.3% | 1.06 k WETH | yellow | yellow | 2 |
| wsrUSD/USDC | 7.38 m USDC | 86.7% | 13.3% | 981.45 k USDC | yellow | yellow | 3 |
| mF-ONE/USDC | 21.39 m USDC | 86.3% | 13.7% | 2.92 m USDC | yellow | red | 1 |
| stUSDS/USDC | 7.01 m USDC | 85.7% | 14.3% | 1.01 m USDC | yellow | yellow | 3 |
| syrupUSDC/RLUSD | 218.75 k RLUSD | 85.1% | 14.9% | 32.63 k RLUSD | yellow | yellow | 6 |
| WBTC/USDT | 107.14 m USDT | 83.6% | 16.4% | 17.55 m USDT | yellow | yellow | 6 |
| wstETH/USDT | 139.13 m USDT | 83.6% | 16.4% | 22.83 m USDT | yellow | yellow | 6 |
| wstETH/WETH | 36.57 k WETH | 81.5% | 18.5% | 6.78 k WETH | yellow | yellow | 3 |
| weETH/RLUSD | 88.98 m RLUSD | 81.4% | 18.6% | 16.57 m RLUSD | yellow | yellow | 7 |
| sUSDS/USDT | 5.24 m USDT | 83.4% | 21.4% | 1.12 m USDT | yellow | yellow | 6 |
| weETH/WETH | 5.04 k WETH | 71.1% | 28.9% | 1.45 k WETH | yellow | yellow | 4 |
| sUSDat/AUSD | 177.78 k AUSD | 70.8% | 29.2% | 51.90 k AUSD | yellow | red | 1 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | green | 4 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.26 | deallocate | allocator: reallocate | 747.54 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.26 | decrease cap | curator: submitCap (a decrease applies at once) | 2.84 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.26 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 2.01 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 14.84 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Sentora RLUSD (`0x71cb2f80`) | v1 | weETH/RLUSD | yellow | n/a | revoke | guardian: revokePendingCap | 75.00 m RLUSD | yellow market: the pending cap exceeds what the market absorbs in 24 hours |

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-reUSD-25JUN2026/USDC | PT past maturity (2026-06-25): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit 5001908
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26348792
