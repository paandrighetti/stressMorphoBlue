# Morpho Blue liquidity sentinel, 2026-10-28

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 13, yellow 10, green 1); not evaluated: 2.
- Tier changes since the previous run: 8.
- Actions listed: 21, for 11 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.27 k USDC | 100.0% | 0.0% | 0.00 USDC | red | red | 2 |
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | red | 6 |
| WBTC/USDT | 90.92 m USDT | 92.8% | 7.2% | 6.58 m USDT | red | red | 3 |
| wstETH/USDT | 122.53 m USDT | 92.7% | 7.3% | 8.99 m USDT | red | red | 3 |
| sUSDS/USDT | 12.38 m USDT | 92.9% | 8.6% | 1.06 m USDT | red | red | 2 |
| wsrUSD/USDC | 9.28 m USDC | 90.6% | 9.4% | 874.08 k USDC | red | yellow | 1 |
| cbBTC/PYUSD | 1.69 m PYUSD | 90.1% | 9.9% | 166.92 k PYUSD | red | red | 9 |
| wstETH/USDC | 33.19 m USDC | 90.1% | 9.9% | 3.30 m USDC | red | red | 4 |
| cbBTC/USDC | 343.90 m USDC | 90.1% | 9.9% | 34.15 m USDC | red | red | 9 |
| WBTC/USDC | 128.49 m USDC | 90.0% | 10.0% | 12.79 m USDC | red | red | 3 |
| sUSDe/PYUSD | 109.65 m PYUSD | 90.0% | 10.0% | 10.93 m PYUSD | red | yellow | 1 |
| stUSDS/USDC | 7.54 m USDC | 90.0% | 10.0% | 752.19 k USDC | red | yellow | 1 |
| weETH/RLUSD | 95.87 m RLUSD | 90.0% | 10.0% | 9.58 m RLUSD | red | red | 2 |
| LBTC/PYUSD | 2.37 k PYUSD | 89.8% | 10.2% | 241.79 PYUSD | yellow | yellow | 9 |
| PT-apyUSD-18JUN2026/USDC | 3.67 m USDC | 89.8% | 10.2% | 374.27 k USDC | yellow | red | 1 |
| AA_FalconXUSDC/USDC | 7.85 m USDC | 89.3% | 10.7% | 839.70 k USDC | yellow | yellow | 9 |
| sUSDe/USDtb | 904.46 k USDtb | 88.2% | 11.8% | 106.75 k USDtb | yellow | red | 1 |
| weETH/PYUSD | 14.60 m PYUSD | 88.2% | 11.8% | 1.73 m PYUSD | yellow | yellow | 5 |
| mF-ONE/USDC | 23.00 m USDC | 86.2% | 13.8% | 3.17 m USDC | yellow | red | 1 |
| wstETH/WETH | 9.58 k WETH | 83.3% | 16.7% | 1.60 k WETH | yellow | yellow | 6 |
| wstETH/WETH | 29.32 k WETH | 83.1% | 16.9% | 4.96 k WETH | yellow | yellow | 6 |
| weETH/WETH | 4.95 k WETH | 82.0% | 18.0% | 891.71 WETH | yellow | yellow | 5 |
| syrupUSDC/RLUSD | 280.58 k RLUSD | 75.6% | 24.4% | 68.38 k RLUSD | yellow | red | 1 |
| sUSDat/AUSD | 438.30 k AUSD | 44.3% | 55.7% | 244.20 k AUSD | green | red | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 36.58 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.21 | deallocate | allocator: reallocate | 6.58 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.21 | decrease cap | curator: submitCap (a decrease applies at once) | 31.16 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.22 | deallocate | allocator: reallocate | 876.80 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.22 | decrease cap | curator: submitCap (a decrease applies at once) | 4.93 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.23 | deallocate | allocator: reallocate | 8.99 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.23 | decrease cap | curator: submitCap (a decrease applies at once) | 39.06 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.39 | deallocate | allocator: reallocate | 3.30 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.39 | decrease cap | curator: submitCap (a decrease applies at once) | 8.54 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | sUSDS/USDT | red | 0.57 | deallocate | allocator: reallocate | 876.80 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | sUSDS/USDT | red | 0.57 | decrease cap | curator: submitCap (a decrease applies at once) | 1.85 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | sUSDS/USDT | red | 0.66 | deallocate | allocator: reallocate | 876.80 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | sUSDS/USDT | red | 0.66 | decrease cap | curator: submitCap (a decrease applies at once) | 1.61 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.78 | deallocate | allocator: reallocate | 876.80 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.78 | decrease cap | curator: submitCap (a decrease applies at once) | 1.36 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 9.72 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Sentora RLUSD (`0x71cb2f80`) | v1 | weETH/RLUSD | red | n/a | revoke | guardian: revokePendingCap | 75.00 m RLUSD | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.40 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.91 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-apxUSD-18JUN2026/USDC | PT past maturity (2026-06-18): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit 5001908
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26290787
