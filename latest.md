# Morpho Blue liquidity sentinel, 2026-11-06

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 7, yellow 16, green 1); not evaluated: 2.
- Tier changes since the previous run: 4.
- Actions listed: 8, for 5 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-apyUSD-18JUN2026/USDC | 3.64 m USDC | 91.0% | 9.0% | 328.53 k USDC | red | yellow | 1 |
| AA_FalconXUSDC/USDC | 5.35 m USDC | 90.4% | 9.6% | 513.32 k USDC | red | red | 4 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.2% | 9.8% | 165.70 k PYUSD | red | red | 17 |
| sUSDe/PYUSD | 115.04 m PYUSD | 90.1% | 9.9% | 11.42 m PYUSD | red | yellow | 1 |
| wstETH/USDC | 39.76 m USDC | 90.1% | 9.9% | 3.96 m USDC | red | yellow | 1 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 8 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 14 |
| cbBTC/USDC | 334.82 m USDC | 90.0% | 10.0% | 33.58 m USDC | yellow | yellow | 2 |
| sUSDe/USDtb | 892.52 k USDtb | 89.6% | 10.4% | 92.96 k USDtb | yellow | yellow | 6 |
| WBTC/USDC | 137.37 m USDC | 89.4% | 10.6% | 14.58 m USDC | yellow | yellow | 2 |
| mF-ONE/USDC | 20.77 m USDC | 88.9% | 11.1% | 2.30 m USDC | yellow | yellow | 2 |
| wsrUSD/USDC | 7.19 m USDC | 88.2% | 11.8% | 846.64 k USDC | yellow | yellow | 4 |
| wstETH/WETH | 33.85 k WETH | 88.1% | 11.9% | 4.04 k WETH | yellow | yellow | 4 |
| syrupUSDC/RLUSD | 213.13 k RLUSD | 87.3% | 12.7% | 27.01 k RLUSD | yellow | yellow | 7 |
| wstETH/WETH | 8.82 k WETH | 86.2% | 13.8% | 1.21 k WETH | yellow | yellow | 3 |
| stUSDS/USDC | 7.03 m USDC | 85.5% | 14.5% | 1.02 m USDC | yellow | yellow | 4 |
| weETH/WETH | 4.21 k WETH | 84.6% | 15.4% | 646.30 WETH | yellow | yellow | 5 |
| weETH/RLUSD | 85.56 m RLUSD | 84.4% | 15.6% | 13.34 m RLUSD | yellow | yellow | 8 |
| weETH/PYUSD | 12.97 m PYUSD | 84.3% | 15.7% | 2.04 m PYUSD | yellow | red | 1 |
| wstETH/USDT | 144.62 m USDT | 83.9% | 16.1% | 23.24 m USDT | yellow | yellow | 7 |
| WBTC/USDT | 98.55 m USDT | 83.9% | 16.1% | 15.85 m USDT | yellow | yellow | 7 |
| sUSDS/USDT | 5.21 m USDT | 83.9% | 20.9% | 1.09 m USDT | yellow | yellow | 7 |
| sUSDat/AUSD | 177.78 k AUSD | 70.8% | 29.2% | 51.90 k AUSD | yellow | yellow | 2 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | green | 5 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.18 | deallocate | allocator: reallocate | 513.32 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.18 | decrease cap | curator: submitCap (a decrease applies at once) | 2.84 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.18 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Steakhouse USDC (`0xbeef0173`) | v1 | wstETH/USDC | red | 0.95 | deallocate | allocator: reallocate | 3.96 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | wstETH/USDC | red | 0.95 | decrease cap | curator: submitCap (a decrease applies at once) | 4.18 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.84 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 13.22 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26354172
