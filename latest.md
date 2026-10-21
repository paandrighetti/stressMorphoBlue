# Morpho Blue liquidity sentinel, 2026-10-21

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 8, yellow 14, green 2); not evaluated: 2.
- Tier changes since the previous run: 1.
- Actions listed: 8, for 6 vaults.
- Vault data: MetaMorpho V1: 163 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.47 k USDC | 91.9% | 8.1% | 200.00 USDC | red | red | 2 |
| PT-apyUSD-18JUN2026/USDC | 3.62 m USDC | 90.8% | 9.2% | 332.94 k USDC | red | red | 2 |
| mF-ONE/USDC | 23.81 m USDC | 90.7% | 9.3% | 2.20 m USDC | red | yellow | 1 |
| weETH/PYUSD | 29.87 m PYUSD | 90.2% | 9.8% | 2.91 m PYUSD | red | red | 2 |
| cbBTC/PYUSD | 1.69 m PYUSD | 90.1% | 9.9% | 167.16 k PYUSD | red | red | 2 |
| wstETH/USDC | 32.56 m USDC | 90.1% | 9.9% | 3.22 m USDC | red | red | 2 |
| cbBTC/USDC | 343.57 m USDC | 90.1% | 9.9% | 34.02 m USDC | red | red | 2 |
| WBTC/USDC | 130.08 m USDC | 90.1% | 9.9% | 12.89 m USDC | red | red | 2 |
| wstETH/WETH | 8.89 k WETH | 89.5% | 10.5% | 933.64 WETH | yellow | yellow | 2 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.3% | 10.7% | 255.47 PYUSD | yellow | yellow | 2 |
| wstETH/WETH | 35.09 k WETH | 89.1% | 10.9% | 3.81 k WETH | yellow | yellow | 2 |
| sUSDe/PYUSD | 109.57 m PYUSD | 89.0% | 11.0% | 12.08 m PYUSD | yellow | yellow | 2 |
| stUSDS/USDC | 7.67 m USDC | 88.8% | 11.2% | 857.22 k USDC | yellow | yellow | 2 |
| AA_FalconXUSDC/USDC | 7.96 m USDC | 88.0% | 12.0% | 953.31 k USDC | yellow | yellow | 2 |
| sUSDe/USDtb | 1.02 m USDtb | 88.6% | 12.4% | 126.61 k USDtb | yellow | yellow | 2 |
| weETH/RLUSD | 101.98 m RLUSD | 87.3% | 12.7% | 12.96 m RLUSD | yellow | yellow | 2 |
| weETH/WETH | 5.66 k WETH | 87.1% | 12.9% | 732.18 WETH | yellow | yellow | 2 |
| wstETH/USDT | 153.49 m USDT | 85.3% | 14.7% | 22.53 m USDT | yellow | yellow | 2 |
| WBTC/USDT | 94.11 m USDT | 85.3% | 14.7% | 13.85 m USDT | yellow | yellow | 2 |
| sUSDS/USDT | 13.57 m USDT | 85.4% | 15.9% | 2.16 m USDT | yellow | yellow | 2 |
| wsrUSD/USDC | 9.11 m USDC | 83.1% | 16.9% | 1.54 m USDC | yellow | yellow | 2 |
| syrupUSDC/RLUSD | 1.20 m RLUSD | 81.8% | 18.2% | 217.83 k RLUSD | yellow | yellow | 2 |
| sUSDat/AUSD | 285.19 k AUSD | 64.9% | 35.1% | 100.22 k AUSD | green | green | 2 |
| stcUSD/USDT | 17.41 USDT | 7.4% | 92.6% | 16.12 USDT | green | green | 2 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.09 | deallocate | allocator: reallocate | 200.00 USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.09 | decrease cap | curator: submitCap (a decrease applies at once) | 2.26 k USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.53 | deallocate | allocator: reallocate | 2.20 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.53 | decrease cap | curator: submitCap (a decrease applies at once) | 4.13 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.25 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.76 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 10.74 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26239935
