# Morpho Blue liquidity sentinel, 2026-10-22

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 15, yellow 8, green 1); not evaluated: 2.
- Tier changes since the previous run: 8.
- Actions listed: 28, for 9 vaults.
- Vault data: MetaMorpho V1: 163 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| sUSDat/AUSD | 195.26 k AUSD | 94.8% | 5.2% | 10.22 k AUSD | red | green | 1 |
| wstETH/WETH | 8.07 k WETH | 94.2% | 5.8% | 471.20 WETH | red | yellow | 1 |
| wstETH/WETH | 30.44 k WETH | 94.1% | 5.9% | 1.79 k WETH | red | yellow | 1 |
| weETH/WETH | 4.94 k WETH | 93.9% | 6.1% | 303.46 WETH | red | yellow | 1 |
| PT-reUSD-25JUN2026/USDC | 2.42 k USDC | 93.8% | 6.2% | 150.00 USDC | red | red | 3 |
| wstETH/USDT | 150.66 m USDT | 91.7% | 8.3% | 12.48 m USDT | red | yellow | 1 |
| WBTC/USDT | 89.31 m USDT | 91.7% | 8.3% | 7.40 m USDT | red | yellow | 1 |
| PT-apyUSD-18JUN2026/USDC | 3.64 m USDC | 90.4% | 9.6% | 350.03 k USDC | red | red | 3 |
| weETH/PYUSD | 29.88 m PYUSD | 90.3% | 9.7% | 2.91 m PYUSD | red | red | 3 |
| sUSDS/USDT | 12.53 m USDT | 91.7% | 9.8% | 1.22 m USDT | red | yellow | 1 |
| cbBTC/USDC | 342.51 m USDC | 90.1% | 9.9% | 33.93 m USDC | red | red | 3 |
| cbBTC/PYUSD | 1.69 m PYUSD | 90.1% | 9.9% | 167.39 k PYUSD | red | red | 3 |
| stUSDS/USDC | 7.60 m USDC | 90.1% | 9.9% | 753.77 k USDC | red | yellow | 1 |
| WBTC/USDC | 130.41 m USDC | 90.1% | 9.9% | 12.95 m USDC | red | red | 3 |
| wstETH/USDC | 32.97 m USDC | 90.0% | 10.0% | 3.30 m USDC | red | red | 3 |
| mF-ONE/USDC | 25.42 m USDC | 89.6% | 10.4% | 2.63 m USDC | yellow | yellow | 3 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.4% | 10.6% | 251.39 PYUSD | yellow | yellow | 3 |
| sUSDe/PYUSD | 109.59 m PYUSD | 89.1% | 10.9% | 11.99 m PYUSD | yellow | yellow | 3 |
| sUSDe/USDtb | 1.02 m USDtb | 88.6% | 12.4% | 126.61 k USDtb | yellow | yellow | 3 |
| AA_FalconXUSDC/USDC | 8.02 m USDC | 87.4% | 12.6% | 1.01 m USDC | yellow | yellow | 3 |
| weETH/RLUSD | 101.98 m RLUSD | 87.3% | 12.7% | 12.96 m RLUSD | yellow | yellow | 3 |
| wsrUSD/USDC | 9.03 m USDC | 85.1% | 14.9% | 1.35 m USDC | yellow | yellow | 3 |
| syrupUSDC/RLUSD | 933.84 k RLUSD | 83.2% | 16.8% | 156.88 k RLUSD | yellow | yellow | 3 |
| stcUSD/USDT | 17.41 USDT | 7.4% | 92.6% | 16.12 USDT | green | green | 3 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.07 | deallocate | allocator: reallocate | 150.00 USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.07 | decrease cap | curator: submitCap (a decrease applies at once) | 2.06 k USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.22 | deallocate | allocator: reallocate | 303.46 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | weETH/WETH | red | 0.22 | decrease cap | curator: submitCap (a decrease applies at once) | 1.35 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.30 | deallocate | allocator: reallocate | 7.40 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.30 | decrease cap | curator: submitCap (a decrease applies at once) | 25.05 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.35 | deallocate | allocator: reallocate | 1.04 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.35 | decrease cap | curator: submitCap (a decrease applies at once) | 3.51 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.39 | deallocate | allocator: reallocate | 303.46 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.39 | decrease cap | curator: submitCap (a decrease applies at once) | 785.17 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | red | 0.39 | revoke | guardian: revokePendingCap | 100.00 k WETH | red market: no cap increase |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.40 | deallocate | allocator: reallocate | 12.48 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.40 | decrease cap | curator: submitCap (a decrease applies at once) | 31.55 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.42 | deallocate | allocator: reallocate | 1.79 k WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.42 | decrease cap | curator: submitCap (a decrease applies at once) | 4.29 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.50 | deallocate | allocator: reallocate | 471.20 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.50 | decrease cap | curator: submitCap (a decrease applies at once) | 948.68 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.65 | deallocate | allocator: reallocate | 1.79 k WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.65 | decrease cap | curator: submitCap (a decrease applies at once) | 2.74 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.67 | deallocate | allocator: reallocate | 471.20 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.67 | decrease cap | curator: submitCap (a decrease applies at once) | 703.51 WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.69 | deallocate | allocator: reallocate | 1.79 k WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | wstETH/WETH | red | 0.69 | decrease cap | curator: submitCap (a decrease applies at once) | 2.58 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| MEV Capital wETH (`0x9a8bc3b0`) | v1 | wstETH/WETH | red | 0.97 | deallocate | allocator: reallocate | 1.79 k WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| MEV Capital wETH (`0x9a8bc3b0`) | v1 | wstETH/WETH | red | 0.97 | decrease cap | curator: submitCap (a decrease applies at once) | 1.86 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 5.78 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.26 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26247416
