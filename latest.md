# Morpho Blue liquidity sentinel, 2026-11-03

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 12, yellow 11, green 1); not evaluated: 2.
- Tier changes since the previous run: 9.
- Actions listed: 16, for 9 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-apyUSD-18JUN2026/USDC | 3.58 m USDC | 92.3% | 7.7% | 274.82 k USDC | red | red | 5 |
| sUSDat/AUSD | 214.04 k AUSD | 90.8% | 9.2% | 19.59 k AUSD | red | red | 5 |
| cbBTC/USDC | 333.46 m USDC | 90.7% | 9.3% | 31.17 m USDC | red | yellow | 1 |
| wstETH/USDC | 33.34 m USDC | 90.6% | 9.4% | 3.13 m USDC | red | yellow | 1 |
| WBTC/USDC | 134.67 m USDC | 90.6% | 9.4% | 12.65 m USDC | red | yellow | 1 |
| AA_FalconXUSDC/USDC | 6.27 m USDC | 90.5% | 9.5% | 594.84 k USDC | red | yellow | 1 |
| mF-ONE/USDC | 23.72 m USDC | 90.4% | 9.6% | 2.27 m USDC | red | red | 5 |
| wstETH/WETH | 8.42 k WETH | 90.3% | 9.7% | 814.14 WETH | red | red | 5 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 5 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.0% | 10.0% | 167.84 k PYUSD | red | red | 14 |
| sUSDe/PYUSD | 115.01 m PYUSD | 90.0% | 10.0% | 11.50 m PYUSD | red | yellow | 1 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 11 |
| sUSDe/USDtb | 892.04 k USDtb | 89.6% | 10.4% | 92.96 k USDtb | yellow | yellow | 3 |
| weETH/WETH | 4.14 k WETH | 89.5% | 10.5% | 436.13 WETH | yellow | yellow | 2 |
| weETH/PYUSD | 14.52 m PYUSD | 89.4% | 10.6% | 1.54 m PYUSD | yellow | red | 1 |
| wstETH/WETH | 34.71 k WETH | 87.9% | 12.1% | 4.20 k WETH | yellow | red | 1 |
| syrupUSDC/RLUSD | 218.70 k RLUSD | 85.1% | 14.9% | 32.63 k RLUSD | yellow | yellow | 4 |
| stUSDS/USDC | 7.04 m USDC | 84.4% | 15.6% | 1.10 m USDC | yellow | red | 1 |
| wstETH/USDT | 127.32 m USDT | 82.6% | 17.4% | 22.21 m USDT | yellow | yellow | 4 |
| WBTC/USDT | 106.12 m USDT | 82.5% | 17.5% | 18.53 m USDT | yellow | yellow | 4 |
| wsrUSD/USDC | 8.00 m USDC | 82.0% | 18.0% | 1.44 m USDC | yellow | red | 1 |
| weETH/RLUSD | 85.77 m RLUSD | 79.2% | 20.8% | 17.83 m RLUSD | yellow | yellow | 5 |
| sUSDS/USDT | 5.62 m USDT | 82.5% | 22.0% | 1.24 m USDT | yellow | yellow | 4 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | green | 2 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.22 | deallocate | allocator: reallocate | 594.84 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.22 | decrease cap | curator: submitCap (a decrease applies at once) | 2.66 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.22 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.38 | deallocate | allocator: reallocate | 814.14 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.38 | decrease cap | curator: submitCap (a decrease applies at once) | 2.12 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.67 | deallocate | allocator: reallocate | 2.27 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.67 | decrease cap | curator: submitCap (a decrease applies at once) | 3.40 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.74 | deallocate | allocator: reallocate | 3.13 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.74 | decrease cap | curator: submitCap (a decrease applies at once) | 4.23 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.76 | deallocate | allocator: reallocate | 12.65 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.76 | decrease cap | curator: submitCap (a decrease applies at once) | 16.65 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | wstETH/WETH | red | 0.85 | deallocate | allocator: reallocate | 814.14 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | wstETH/WETH | red | 0.85 | decrease cap | curator: submitCap (a decrease applies at once) | 961.63 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.60 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 15.36 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26334134
