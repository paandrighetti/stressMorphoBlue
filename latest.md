# Morpho Blue liquidity sentinel, 2026-11-07

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 13, yellow 9, green 2); not evaluated: 2.
- Tier changes since the previous run: 7.
- Actions listed: 18, for 8 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| wstETH/USDT | 117.35 m USDT | 92.3% | 7.7% | 9.00 m USDT | red | yellow | 1 |
| cbBTC/USDC | 331.10 m USDC | 92.3% | 7.7% | 25.40 m USDC | red | yellow | 1 |
| WBTC/USDT | 90.08 m USDT | 92.3% | 7.7% | 6.93 m USDT | red | yellow | 1 |
| AA_FalconXUSDC/USDC | 5.24 m USDC | 92.3% | 7.7% | 403.01 k USDC | red | red | 5 |
| WBTC/USDC | 133.25 m USDC | 92.3% | 7.7% | 10.28 m USDC | red | yellow | 1 |
| wstETH/USDC | 38.49 m USDC | 92.3% | 7.7% | 2.97 m USDC | red | red | 2 |
| mF-ONE/USDC | 20.27 m USDC | 91.1% | 8.9% | 1.79 m USDC | red | yellow | 1 |
| wsrUSD/USDC | 7.20 m USDC | 90.9% | 9.1% | 654.62 k USDC | red | yellow | 1 |
| PT-apyUSD-18JUN2026/USDC | 3.66 m USDC | 90.5% | 9.5% | 348.53 k USDC | red | red | 2 |
| sUSDe/PYUSD | 115.05 m PYUSD | 90.4% | 9.6% | 11.10 m PYUSD | red | red | 2 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.2% | 9.8% | 165.28 k PYUSD | red | red | 18 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 9 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 15 |
| sUSDe/USDtb | 892.52 k USDtb | 89.6% | 10.4% | 92.96 k USDtb | yellow | yellow | 7 |
| wstETH/WETH | 34.45 k WETH | 88.3% | 11.7% | 4.04 k WETH | yellow | yellow | 5 |
| syrupUSDC/RLUSD | 211.96 k RLUSD | 87.8% | 12.2% | 25.81 k RLUSD | yellow | yellow | 8 |
| wstETH/WETH | 8.87 k WETH | 87.7% | 12.3% | 1.09 k WETH | yellow | yellow | 4 |
| weETH/RLUSD | 82.51 m RLUSD | 87.2% | 12.8% | 10.59 m RLUSD | yellow | yellow | 9 |
| stUSDS/USDC | 7.01 m USDC | 86.6% | 13.4% | 938.53 k USDC | yellow | yellow | 5 |
| sUSDS/USDT | 4.29 m USDT | 92.3% | 13.6% | 583.06 k USDT | yellow | yellow | 8 |
| weETH/PYUSD | 8.83 m PYUSD | 85.4% | 14.6% | 1.29 m PYUSD | yellow | yellow | 2 |
| weETH/WETH | 4.18 k WETH | 85.3% | 14.7% | 615.95 WETH | yellow | yellow | 6 |
| sUSDat/AUSD | 158.70 k AUSD | 47.5% | 52.5% | 83.28 k AUSD | green | yellow | 1 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | green | 6 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.14 | deallocate | allocator: reallocate | 403.01 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.14 | decrease cap | curator: submitCap (a decrease applies at once) | 2.94 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.14 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.19 | deallocate | allocator: reallocate | 6.93 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.19 | decrease cap | curator: submitCap (a decrease applies at once) | 36.17 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.30 | deallocate | allocator: reallocate | 9.00 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.30 | decrease cap | curator: submitCap (a decrease applies at once) | 29.93 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.56 | deallocate | allocator: reallocate | 1.79 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.56 | decrease cap | curator: submitCap (a decrease applies at once) | 3.19 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDC (`0xbeef0173`) | v1 | cbBTC/USDC | red | 0.86 | deallocate | allocator: reallocate | 25.40 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | cbBTC/USDC | red | 0.86 | decrease cap | curator: submitCap (a decrease applies at once) | 29.49 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.88 | deallocate | allocator: reallocate | 10.28 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.88 | decrease cap | curator: submitCap (a decrease applies at once) | 11.65 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC Prime (`0xdd0f28e1`) | v1 | wstETH/USDC | red | 0.98 | deallocate | allocator: reallocate | 2.97 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC Prime (`0xdd0f28e1`) | v1 | wstETH/USDC | red | 0.98 | decrease cap | curator: submitCap (a decrease applies at once) | 3.02 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 4.41 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.80 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26362535
