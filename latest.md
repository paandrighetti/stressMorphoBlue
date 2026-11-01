# Morpho Blue liquidity sentinel, 2026-11-01

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 23 (red 14, yellow 9, green 0); not evaluated: 3.
- Tier changes since the previous run: 2.
- Actions listed: 16, for 8 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-apyUSD-18JUN2026/USDC | 3.58 m USDC | 92.4% | 7.6% | 271.85 k USDC | red | red | 3 |
| weETH/WETH | 4.17 k WETH | 91.8% | 8.2% | 340.86 WETH | red | red | 3 |
| mF-ONE/USDC | 22.34 m USDC | 91.2% | 8.8% | 1.96 m USDC | red | red | 3 |
| sUSDat/AUSD | 213.78 k AUSD | 90.9% | 9.1% | 19.55 k AUSD | red | red | 3 |
| wstETH/WETH | 8.38 k WETH | 90.7% | 9.3% | 781.20 WETH | red | red | 3 |
| stUSDS/USDC | 6.11 m USDC | 90.6% | 9.4% | 573.41 k USDC | red | yellow | 1 |
| weETH/PYUSD | 14.46 m PYUSD | 90.5% | 9.5% | 1.38 m PYUSD | red | red | 3 |
| AA_FalconXUSDC/USDC | 7.76 m USDC | 90.4% | 9.6% | 746.80 k USDC | red | red | 2 |
| WBTC/USDC | 135.73 m USDC | 90.1% | 9.9% | 13.39 m USDC | red | red | 2 |
| cbBTC/USDC | 235.63 m USDC | 90.1% | 9.9% | 23.25 m USDC | red | red | 2 |
| wstETH/USDC | 33.29 m USDC | 90.1% | 9.9% | 3.30 m USDC | red | red | 2 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.99 PYUSD | red | red | 3 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.0% | 10.0% | 168.08 k PYUSD | red | red | 12 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 9 |
| sUSDe/USDtb | 888.38 k USDtb | 89.9% | 10.1% | 89.62 k USDtb | yellow | red | 1 |
| sUSDe/PYUSD | 114.99 m PYUSD | 89.9% | 10.1% | 11.61 m PYUSD | yellow | yellow | 2 |
| wstETH/WETH | 32.48 k WETH | 89.6% | 10.4% | 3.37 k WETH | yellow | yellow | 2 |
| wsrUSD/USDC | 7.59 m USDC | 89.5% | 10.5% | 799.62 k USDC | yellow | yellow | 2 |
| weETH/RLUSD | 78.13 m RLUSD | 87.3% | 12.7% | 9.93 m RLUSD | yellow | yellow | 3 |
| wstETH/USDT | 130.79 m USDT | 81.4% | 18.6% | 24.37 m USDT | yellow | yellow | 2 |
| WBTC/USDT | 106.57 m USDT | 81.3% | 18.7% | 19.88 m USDT | yellow | yellow | 2 |
| syrupUSDC/RLUSD | 234.22 k RLUSD | 79.4% | 20.6% | 48.21 k RLUSD | yellow | yellow | 2 |
| sUSDS/USDT | 5.19 m USDT | 81.2% | 23.7% | 1.23 m USDT | yellow | yellow | 2 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.28 | deallocate | allocator: reallocate | 340.86 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.28 | decrease cap | curator: submitCap (a decrease applies at once) | 1.20 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.37 | deallocate | allocator: reallocate | 781.20 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.37 | decrease cap | curator: submitCap (a decrease applies at once) | 2.13 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.40 | deallocate | allocator: reallocate | 746.80 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.40 | decrease cap | curator: submitCap (a decrease applies at once) | 1.86 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.40 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.47 | deallocate | allocator: reallocate | 340.86 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.47 | decrease cap | curator: submitCap (a decrease applies at once) | 724.07 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.47 | revoke | guardian: revokePendingCap | 100.00 k WETH | red market: no cap increase |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.51 | deallocate | allocator: reallocate | 13.39 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.51 | decrease cap | curator: submitCap (a decrease applies at once) | 26.37 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.53 | deallocate | allocator: reallocate | 1.96 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.53 | decrease cap | curator: submitCap (a decrease applies at once) | 3.72 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 16.47 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Sentora RLUSD (`0x71cb2f80`) | v1 | weETH/RLUSD | yellow | n/a | revoke | guardian: revokePendingCap | 75.00 m RLUSD | yellow market: the pending cap exceeds what the market absorbs in 24 hours |

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-apxUSD-18JUN2026/USDC | PT past maturity (2026-06-18): exit is par redemption, AMM depth not applicable |
| PT-reUSD-25JUN2026/USDC | PT past maturity (2026-06-25): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit 5001908
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26319481
