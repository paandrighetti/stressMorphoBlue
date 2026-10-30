# Morpho Blue liquidity sentinel, 2026-10-30

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 18, yellow 6, green 0); not evaluated: 2.
- Tier changes since the previous run: 15.
- Actions listed: 53, for 20 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.28 k USDC | 100.0% | 0.0% | 0.00 USDC | red | red | 3 |
| PT-apyUSD-18JUN2026/USDC | 3.30 m USDC | 100.0% | 0.0% | 997.55 USDC | red | yellow | 1 |
| wstETH/WETH | 29.47 k WETH | 98.3% | 1.7% | 502.17 WETH | red | yellow | 1 |
| wstETH/WETH | 8.14 k WETH | 97.9% | 2.1% | 169.13 WETH | red | yellow | 1 |
| mF-ONE/USDC | 20.74 m USDC | 96.3% | 3.7% | 766.79 k USDC | red | yellow | 1 |
| weETH/WETH | 3.99 k WETH | 96.0% | 4.0% | 160.10 WETH | red | yellow | 1 |
| weETH/PYUSD | 13.60 m PYUSD | 93.9% | 6.1% | 823.40 k PYUSD | red | yellow | 1 |
| LBTC/PYUSD | 2.28 k PYUSD | 93.5% | 6.5% | 148.82 PYUSD | red | yellow | 1 |
| cbBTC/PYUSD | 1.63 m PYUSD | 93.0% | 7.0% | 113.60 k PYUSD | red | red | 10 |
| sUSDe/PYUSD | 108.86 m PYUSD | 92.7% | 7.3% | 7.89 m PYUSD | red | red | 2 |
| wstETH/USDT | 110.55 m USDT | 92.1% | 7.9% | 8.69 m USDT | red | red | 4 |
| WBTC/USDT | 92.22 m USDT | 91.9% | 8.1% | 7.44 m USDT | red | red | 4 |
| wsrUSD/USDC | 7.99 m USDC | 90.9% | 9.1% | 728.86 k USDC | red | red | 2 |
| sUSDe/USDtb | 879.78 k USDtb | 90.7% | 9.3% | 81.64 k USDtb | red | yellow | 1 |
| syrupUSDC/RLUSD | 234.17 k RLUSD | 90.6% | 9.4% | 21.93 k RLUSD | red | yellow | 1 |
| sUSDS/USDT | 10.75 m USDT | 92.2% | 9.5% | 1.02 m USDT | red | red | 3 |
| sUSDat/AUSD | 215.71 k AUSD | 90.0% | 10.0% | 21.56 k AUSD | red | green | 1 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 7 |
| stUSDS/USDC | 5.89 m USDC | 89.5% | 10.5% | 615.26 k USDC | yellow | red | 1 |
| weETH/RLUSD | 78.13 m RLUSD | 89.2% | 10.8% | 8.43 m RLUSD | yellow | red | 1 |
| wstETH/USDC | 37.87 m USDC | 79.8% | 20.2% | 7.66 m USDC | yellow | red | 1 |
| cbBTC/USDC | 177.84 m USDC | 79.6% | 20.4% | 36.31 m USDC | yellow | red | 1 |
| WBTC/USDC | 153.33 m USDC | 79.4% | 20.6% | 31.60 m USDC | yellow | red | 1 |
| AA_FalconXUSDC/USDC | 9.16 m USDC | 76.6% | 23.4% | 2.14 m USDC | yellow | yellow | 10 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 36.66 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | deallocate | allocator: reallocate | 81.64 k USDtb | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | decrease cap | curator: submitCap (a decrease applies at once) | 809.36 k USDtb | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.11 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.11 | decrease cap | curator: submitCap (a decrease applies at once) | 4.44 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.13 | deallocate | allocator: reallocate | 160.10 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.13 | decrease cap | curator: submitCap (a decrease applies at once) | 1.20 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.18 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.18 | decrease cap | curator: submitCap (a decrease applies at once) | 2.80 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.19 | deallocate | allocator: reallocate | 169.13 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.19 | decrease cap | curator: submitCap (a decrease applies at once) | 889.72 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.21 | deallocate | allocator: reallocate | 766.79 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.21 | decrease cap | curator: submitCap (a decrease applies at once) | 3.70 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.21 | deallocate | allocator: reallocate | 838.24 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.21 | decrease cap | curator: submitCap (a decrease applies at once) | 4.90 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.22 | deallocate | allocator: reallocate | 7.44 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.22 | decrease cap | curator: submitCap (a decrease applies at once) | 33.86 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.22 | deallocate | allocator: reallocate | 160.10 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.22 | decrease cap | curator: submitCap (a decrease applies at once) | 723.95 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.22 | revoke | guardian: revokePendingCap | 100.00 k WETH | red market: no cap increase |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.23 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.23 | decrease cap | curator: submitCap (a decrease applies at once) | 2.22 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.23 | deallocate | allocator: reallocate | 8.69 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.23 | decrease cap | curator: submitCap (a decrease applies at once) | 37.03 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| MEV Capital wETH (`0x9a8bc3b0`) | v1 | wstETH/WETH | red | 0.27 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| MEV Capital wETH (`0x9a8bc3b0`) | v1 | wstETH/WETH | red | 0.27 | decrease cap | curator: submitCap (a decrease applies at once) | 1.86 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | wstETH/WETH | red | 0.33 | deallocate | allocator: reallocate | 169.13 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | wstETH/WETH | red | 0.33 | decrease cap | curator: submitCap (a decrease applies at once) | 520.22 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | weETH/WETH | red | 0.50 | deallocate | allocator: reallocate | 160.10 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| WETH ARM Vault (`0x3dfe70b0`) | v1 | weETH/WETH | red | 0.50 | decrease cap | curator: submitCap (a decrease applies at once) | 322.14 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Re7 WETH (`0x78fc2c2e`) | v1 | wstETH/WETH | red | 0.59 | deallocate | allocator: reallocate | 169.13 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Re7 WETH (`0x78fc2c2e`) | v1 | wstETH/WETH | red | 0.59 | decrease cap | curator: submitCap (a decrease applies at once) | 288.39 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | sUSDS/USDT | red | 0.63 | deallocate | allocator: reallocate | 838.24 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | sUSDS/USDT | red | 0.63 | decrease cap | curator: submitCap (a decrease applies at once) | 1.61 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Index Coop hyETH (`0x70190728`) | v1 | wstETH/WETH | red | 0.70 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Index Coop hyETH (`0x70190728`) | v1 | wstETH/WETH | red | 0.70 | decrease cap | curator: submitCap (a decrease applies at once) | 714.70 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet LRT Core (`0x4881ef0b`) | v1 | weETH/WETH | red | 0.76 | deallocate | allocator: reallocate | 160.10 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet LRT Core (`0x4881ef0b`) | v1 | weETH/WETH | red | 0.76 | decrease cap | curator: submitCap (a decrease applies at once) | 210.48 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet LRT Core (`0x4881ef0b`) | v1 | wstETH/WETH | red | 0.77 | deallocate | allocator: reallocate | 502.17 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet LRT Core (`0x4881ef0b`) | v1 | wstETH/WETH | red | 0.77 | decrease cap | curator: submitCap (a decrease applies at once) | 652.31 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | sUSDS/USDT | red | 0.79 | deallocate | allocator: reallocate | 838.24 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | sUSDS/USDT | red | 0.79 | decrease cap | curator: submitCap (a decrease applies at once) | 1.30 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.90 | deallocate | allocator: reallocate | 838.24 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.90 | decrease cap | curator: submitCap (a decrease applies at once) | 1.13 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
|  Usual Boosted USDC (`0xd6307011`) | v1 | mF-ONE/USDC | red | 0.90 | deallocate | allocator: reallocate | 766.79 k USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
|  Usual Boosted USDC (`0xd6307011`) | v1 | mF-ONE/USDC | red | 0.90 | decrease cap | curator: submitCap (a decrease applies at once) | 848.11 k USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.98 | deallocate | allocator: reallocate | 169.13 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.98 | decrease cap | curator: submitCap (a decrease applies at once) | 172.40 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 11.89 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.99 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26305133
