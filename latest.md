# Morpho Blue liquidity sentinel, 2026-11-04

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 11, yellow 12, green 1); not evaluated: 2.
- Tier changes since the previous run: 1.
- Actions listed: 10, for 6 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| sUSDat/AUSD | 214.04 k AUSD | 90.8% | 9.2% | 19.59 k AUSD | red | red | 6 |
| cbBTC/USDC | 331.99 m USDC | 90.6% | 9.4% | 31.09 m USDC | red | red | 2 |
| WBTC/USDC | 135.23 m USDC | 90.4% | 9.6% | 12.93 m USDC | red | red | 2 |
| wstETH/USDC | 33.42 m USDC | 90.4% | 9.6% | 3.21 m USDC | red | red | 2 |
| mF-ONE/USDC | 22.97 m USDC | 90.4% | 9.6% | 2.21 m USDC | red | red | 6 |
| AA_FalconXUSDC/USDC | 6.97 m USDC | 90.3% | 9.7% | 678.32 k USDC | red | red | 2 |
| sUSDe/PYUSD | 115.02 m PYUSD | 90.1% | 9.9% | 11.40 m PYUSD | red | red | 2 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 6 |
| PT-apyUSD-18JUN2026/USDC | 3.67 m USDC | 90.0% | 10.0% | 365.95 k USDC | red | red | 6 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.0% | 10.0% | 168.04 k PYUSD | red | red | 15 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 12 |
| sUSDe/USDtb | 892.04 k USDtb | 89.6% | 10.4% | 92.96 k USDtb | yellow | yellow | 4 |
| weETH/PYUSD | 14.52 m PYUSD | 89.4% | 10.6% | 1.54 m PYUSD | yellow | yellow | 2 |
| syrupUSDC/RLUSD | 218.71 k RLUSD | 85.1% | 14.9% | 32.63 k RLUSD | yellow | yellow | 5 |
| wsrUSD/USDC | 7.66 m USDC | 83.6% | 16.4% | 1.26 m USDC | yellow | yellow | 2 |
| wstETH/USDT | 129.26 m USDT | 83.0% | 17.0% | 22.02 m USDT | yellow | yellow | 5 |
| WBTC/USDT | 107.18 m USDT | 83.0% | 17.0% | 18.27 m USDT | yellow | yellow | 5 |
| wstETH/WETH | 36.55 k WETH | 82.5% | 17.5% | 6.39 k WETH | yellow | yellow | 2 |
| stUSDS/USDC | 7.04 m USDC | 82.0% | 18.0% | 1.26 m USDC | yellow | yellow | 2 |
| weETH/RLUSD | 88.97 m RLUSD | 81.1% | 18.9% | 16.82 m RLUSD | yellow | yellow | 6 |
| wstETH/WETH | 9.41 k WETH | 80.8% | 19.2% | 1.81 k WETH | yellow | red | 1 |
| weETH/WETH | 4.58 k WETH | 78.1% | 21.9% | 1.00 k WETH | yellow | yellow | 3 |
| sUSDS/USDT | 5.35 m USDT | 82.8% | 21.9% | 1.17 m USDT | yellow | yellow | 5 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | green | 3 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.23 | deallocate | allocator: reallocate | 678.32 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.23 | decrease cap | curator: submitCap (a decrease applies at once) | 2.96 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.23 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.61 | deallocate | allocator: reallocate | 2.21 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.61 | decrease cap | curator: submitCap (a decrease applies at once) | 3.62 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.73 | deallocate | allocator: reallocate | 12.93 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.73 | decrease cap | curator: submitCap (a decrease applies at once) | 17.72 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 1.38 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 15.49 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26339807
