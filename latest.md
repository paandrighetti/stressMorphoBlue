# Morpho Blue liquidity sentinel, 2026-10-23

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 12, yellow 11, green 1); not evaluated: 2.
- Tier changes since the previous run: 7.
- Actions listed: 12, for 8 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.27 k USDC | 100.0% | 0.0% | 0.00 USDC | red | red | 4 |
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | green | 1 |
| sUSDe/USDtb | 936.09 k USDtb | 96.4% | 4.8% | 44.51 k USDtb | red | yellow | 1 |
| sUSDat/AUSD | 209.99 k AUSD | 90.8% | 9.2% | 19.39 k AUSD | red | red | 2 |
| wstETH/USDT | 152.02 m USDT | 90.5% | 9.5% | 14.51 m USDT | red | red | 2 |
| WBTC/USDT | 91.52 m USDT | 90.5% | 9.5% | 8.74 m USDT | red | red | 2 |
| weETH/PYUSD | 29.89 m PYUSD | 90.1% | 9.9% | 2.94 m PYUSD | red | red | 4 |
| wstETH/USDC | 32.95 m USDC | 90.1% | 9.9% | 3.26 m USDC | red | red | 4 |
| cbBTC/USDC | 343.23 m USDC | 90.1% | 9.9% | 34.02 m USDC | red | red | 4 |
| stUSDS/USDC | 7.60 m USDC | 90.1% | 9.9% | 753.77 k USDC | red | red | 2 |
| WBTC/USDC | 128.45 m USDC | 90.1% | 9.9% | 12.75 m USDC | red | red | 4 |
| cbBTC/PYUSD | 1.69 m PYUSD | 90.0% | 10.0% | 168.89 k PYUSD | red | red | 4 |
| PT-apyUSD-18JUN2026/USDC | 3.68 m USDC | 89.6% | 10.4% | 383.04 k USDC | yellow | red | 1 |
| mF-ONE/USDC | 24.48 m USDC | 89.5% | 10.5% | 2.58 m USDC | yellow | yellow | 4 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.4% | 10.6% | 251.39 PYUSD | yellow | yellow | 4 |
| sUSDe/PYUSD | 109.59 m PYUSD | 89.1% | 10.9% | 11.99 m PYUSD | yellow | yellow | 4 |
| sUSDS/USDT | 12.71 m USDT | 90.5% | 11.0% | 1.40 m USDT | yellow | red | 1 |
| weETH/RLUSD | 100.32 m RLUSD | 88.6% | 11.4% | 11.48 m RLUSD | yellow | yellow | 4 |
| AA_FalconXUSDC/USDC | 7.93 m USDC | 88.4% | 11.6% | 919.73 k USDC | yellow | yellow | 4 |
| syrupUSDC/RLUSD | 902.15 k RLUSD | 86.1% | 13.9% | 125.11 k RLUSD | yellow | yellow | 4 |
| wsrUSD/USDC | 8.99 m USDC | 85.5% | 14.5% | 1.30 m USDC | yellow | yellow | 4 |
| wstETH/WETH | 9.01 k WETH | 84.5% | 15.5% | 1.40 k WETH | yellow | red | 1 |
| wstETH/WETH | 28.95 k WETH | 81.7% | 18.3% | 5.31 k WETH | yellow | red | 1 |
| weETH/WETH | 6.67 k WETH | 67.4% | 32.6% | 2.17 k WETH | green | red | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.91 k USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.05 | deallocate | allocator: reallocate | 33.49 k USDtb | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.05 | decrease cap | curator: submitCap (a decrease applies at once) | 825.82 k USDtb | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.35 | deallocate | allocator: reallocate | 8.74 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.35 | decrease cap | curator: submitCap (a decrease applies at once) | 25.06 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.46 | deallocate | allocator: reallocate | 14.51 m USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.46 | decrease cap | curator: submitCap (a decrease applies at once) | 31.50 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 6.82 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.24 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26254587
