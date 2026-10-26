# Morpho Blue liquidity sentinel, 2026-10-26

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 11, yellow 13, green 0); not evaluated: 2.
- Tier changes since the previous run: 6.
- Actions listed: 10, for 6 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | red | 4 |
| sUSDat/AUSD | 207.55 k AUSD | 93.4% | 6.6% | 13.68 k AUSD | red | red | 5 |
| WBTC/USDT | 91.64 m USDT | 91.5% | 8.5% | 7.83 m USDT | red | yellow | 1 |
| wstETH/USDT | 149.68 m USDT | 91.5% | 8.5% | 12.79 m USDT | red | yellow | 1 |
| mF-ONE/USDC | 25.51 m USDC | 90.8% | 9.2% | 2.36 m USDC | red | yellow | 1 |
| stUSDS/USDC | 7.50 m USDC | 90.5% | 9.5% | 712.19 k USDC | red | yellow | 1 |
| wsrUSD/USDC | 8.64 m USDC | 90.2% | 9.8% | 845.35 k USDC | red | red | 2 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.1% | 9.9% | 166.24 k PYUSD | red | red | 7 |
| wstETH/USDC | 32.92 m USDC | 90.1% | 9.9% | 3.26 m USDC | red | red | 2 |
| cbBTC/USDC | 343.30 m USDC | 90.1% | 9.9% | 34.07 m USDC | red | red | 7 |
| WBTC/USDC | 128.34 m USDC | 90.1% | 9.9% | 12.77 m USDC | red | yellow | 1 |
| sUSDS/USDT | 12.58 m USDT | 91.5% | 10.0% | 1.26 m USDT | yellow | yellow | 4 |
| PT-apyUSD-18JUN2026/USDC | 3.66 m USDC | 90.0% | 10.0% | 367.33 k USDC | yellow | red | 1 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.7% | 10.3% | 243.69 PYUSD | yellow | yellow | 7 |
| weETH/RLUSD | 100.54 m RLUSD | 89.5% | 10.5% | 10.60 m RLUSD | yellow | yellow | 7 |
| sUSDe/PYUSD | 109.59 m PYUSD | 89.1% | 10.9% | 11.99 m PYUSD | yellow | yellow | 7 |
| AA_FalconXUSDC/USDC | 7.95 m USDC | 88.2% | 11.8% | 939.51 k USDC | yellow | yellow | 7 |
| weETH/PYUSD | 15.35 m PYUSD | 86.7% | 13.3% | 2.04 m PYUSD | yellow | yellow | 3 |
| sUSDe/USDtb | 924.22 k USDtb | 87.5% | 13.7% | 126.79 k USDtb | yellow | yellow | 2 |
| syrupUSDC/RLUSD | 902.45 k RLUSD | 86.1% | 13.9% | 125.11 k RLUSD | yellow | yellow | 7 |
| wstETH/WETH | 9.44 k WETH | 84.5% | 15.5% | 1.46 k WETH | yellow | yellow | 4 |
| wstETH/WETH | 28.70 k WETH | 84.2% | 15.8% | 4.52 k WETH | yellow | yellow | 4 |
| weETH/WETH | 5.13 k WETH | 82.8% | 17.2% | 880.74 WETH | yellow | yellow | 3 |
| PT-reUSD-25JUN2026/USDC | 2.75 k USDC | 82.6% | 17.4% | 479.16 USDC | yellow | yellow | 2 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.29 | deallocate | allocator: reallocate | 7.83 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.29 | decrease cap | curator: submitCap (a decrease applies at once) | 27.23 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.36 | deallocate | allocator: reallocate | 12.79 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.36 | decrease cap | curator: submitCap (a decrease applies at once) | 35.46 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.74 | deallocate | allocator: reallocate | 2.36 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.74 | decrease cap | curator: submitCap (a decrease applies at once) | 3.18 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 10.42 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.28 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.87 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Sentora RLUSD (`0x71cb2f80`) | v1 | weETH/RLUSD | yellow | n/a | revoke | guardian: revokePendingCap | 75.00 m RLUSD | yellow market: the pending cap exceeds what the market absorbs in 24 hours |

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-apxUSD-18JUN2026/USDC | PT past maturity (2026-06-18): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit 5001908
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26276421
