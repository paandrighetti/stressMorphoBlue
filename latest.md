# Morpho Blue liquidity sentinel, 2026-10-31

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 15, yellow 9, green 0); not evaluated: 2.
- Tier changes since the previous run: 11.
- Actions listed: 25, for 14 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.28 k USDC | 100.0% | 0.0% | 0.00 USDC | red | red | 4 |
| wstETH/WETH | 8.13 k WETH | 93.5% | 6.5% | 529.31 WETH | red | red | 2 |
| PT-apyUSD-18JUN2026/USDC | 3.55 m USDC | 92.9% | 7.1% | 250.84 k USDC | red | red | 2 |
| mF-ONE/USDC | 22.25 m USDC | 91.6% | 8.4% | 1.87 m USDC | red | red | 2 |
| sUSDe/USDtb | 873.09 k USDtb | 91.5% | 8.5% | 74.62 k USDtb | red | red | 2 |
| wstETH/USDC | 32.90 m USDC | 91.1% | 8.9% | 2.93 m USDC | red | yellow | 1 |
| sUSDat/AUSD | 213.78 k AUSD | 90.9% | 9.1% | 19.55 k AUSD | red | red | 2 |
| WBTC/USDC | 134.69 m USDC | 90.9% | 9.1% | 12.32 m USDC | red | yellow | 1 |
| cbBTC/USDC | 234.25 m USDC | 90.8% | 9.2% | 21.52 m USDC | red | yellow | 1 |
| weETH/WETH | 4.22 k WETH | 90.6% | 9.4% | 395.63 WETH | red | red | 2 |
| AA_FalconXUSDC/USDC | 7.74 m USDC | 90.6% | 9.4% | 725.10 k USDC | red | yellow | 1 |
| weETH/PYUSD | 14.45 m PYUSD | 90.5% | 9.5% | 1.37 m PYUSD | red | red | 2 |
| LBTC/PYUSD | 2.37 k PYUSD | 90.0% | 10.0% | 236.18 PYUSD | red | red | 2 |
| cbBTC/PYUSD | 1.71 m PYUSD | 90.0% | 10.0% | 170.79 k PYUSD | red | red | 11 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 8 |
| sUSDe/PYUSD | 114.64 m PYUSD | 89.7% | 10.3% | 11.82 m PYUSD | yellow | red | 1 |
| wsrUSD/USDC | 7.68 m USDC | 89.3% | 10.7% | 821.36 k USDC | yellow | red | 1 |
| wstETH/WETH | 33.91 k WETH | 88.0% | 12.0% | 4.08 k WETH | yellow | red | 1 |
| weETH/RLUSD | 78.13 m RLUSD | 87.3% | 12.7% | 9.93 m RLUSD | yellow | yellow | 2 |
| stUSDS/USDC | 6.11 m USDC | 86.3% | 13.7% | 837.79 k USDC | yellow | yellow | 2 |
| wstETH/USDT | 130.39 m USDT | 80.7% | 19.3% | 25.15 m USDT | yellow | red | 1 |
| WBTC/USDT | 107.23 m USDT | 80.7% | 19.3% | 20.71 m USDT | yellow | red | 1 |
| syrupUSDC/RLUSD | 234.21 k RLUSD | 79.4% | 20.6% | 48.21 k RLUSD | yellow | red | 1 |
| sUSDS/USDT | 5.30 m USDT | 79.6% | 25.2% | 1.33 m USDT | yellow | red | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 36.71 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | deallocate | allocator: reallocate | 74.62 k USDtb | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | decrease cap | curator: submitCap (a decrease applies at once) | 757.40 k USDtb | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.33 | deallocate | allocator: reallocate | 395.63 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.33 | decrease cap | curator: submitCap (a decrease applies at once) | 1.20 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.35 | deallocate | allocator: reallocate | 529.31 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.35 | decrease cap | curator: submitCap (a decrease applies at once) | 1.52 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.42 | deallocate | allocator: reallocate | 725.10 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.42 | decrease cap | curator: submitCap (a decrease applies at once) | 1.75 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | red | 0.42 | revoke | guardian: revokePendingCap | 40.00 m USDC | red market: no cap increase |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.46 | deallocate | allocator: reallocate | 12.32 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDC (`0xbeef0173`) | v1 | WBTC/USDC | red | 0.46 | decrease cap | curator: submitCap (a decrease applies at once) | 26.60 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.50 | deallocate | allocator: reallocate | 1.87 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.50 | decrease cap | curator: submitCap (a decrease applies at once) | 3.71 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.55 | deallocate | allocator: reallocate | 395.63 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.55 | decrease cap | curator: submitCap (a decrease applies at once) | 724.00 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.55 | revoke | guardian: revokePendingCap | 100.00 k WETH | red market: no cap increase |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | weETH/WETH | red | 0.70 | deallocate | allocator: reallocate | 395.63 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | weETH/WETH | red | 0.70 | decrease cap | curator: submitCap (a decrease applies at once) | 566.78 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.75 | deallocate | allocator: reallocate | 2.93 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.75 | decrease cap | curator: submitCap (a decrease applies at once) | 3.91 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 17.16 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26312006
