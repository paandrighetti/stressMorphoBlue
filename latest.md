# Morpho Blue liquidity sentinel, 2026-10-27

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 15, yellow 9, green 0); not evaluated: 2.
- Tier changes since the previous run: 8.
- Actions listed: 61, for 20 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.27 k USDC | 100.0% | 0.0% | 0.00 USDC | red | yellow | 1 |
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | red | 5 |
| WBTC/USDT | 84.01 m USDT | 100.0% | 0.0% | 840.09 USDT | red | red | 2 |
| wstETH/USDT | 128.25 m USDT | 100.0% | 0.0% | 1.44 k USDT | red | red | 2 |
| sUSDS/USDT | 11.50 m USDT | 100.0% | 1.6% | 184.72 k USDT | red | yellow | 1 |
| syrupUSDC/RLUSD | 818.52 k RLUSD | 95.0% | 5.0% | 41.04 k RLUSD | red | yellow | 1 |
| weETH/RLUSD | 95.11 m RLUSD | 94.3% | 5.7% | 5.45 m RLUSD | red | yellow | 1 |
| sUSDat/AUSD | 208.19 k AUSD | 93.2% | 6.8% | 14.23 k AUSD | red | red | 6 |
| mF-ONE/USDC | 24.72 m USDC | 92.7% | 7.3% | 1.81 m USDC | red | red | 2 |
| PT-apyUSD-18JUN2026/USDC | 3.61 m USDC | 91.3% | 8.7% | 315.28 k USDC | red | yellow | 1 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.4% | 9.6% | 162.14 k PYUSD | red | red | 8 |
| sUSDe/USDtb | 884.37 k USDtb | 91.4% | 9.8% | 86.76 k USDtb | red | yellow | 1 |
| wstETH/USDC | 33.05 m USDC | 90.1% | 9.9% | 3.28 m USDC | red | red | 3 |
| cbBTC/USDC | 342.56 m USDC | 90.1% | 9.9% | 34.01 m USDC | red | red | 8 |
| WBTC/USDC | 128.17 m USDC | 90.1% | 9.9% | 12.72 m USDC | red | red | 2 |
| LBTC/PYUSD | 2.37 k PYUSD | 89.8% | 10.2% | 242.96 PYUSD | yellow | yellow | 8 |
| sUSDe/PYUSD | 109.65 m PYUSD | 89.3% | 10.7% | 11.68 m PYUSD | yellow | yellow | 8 |
| AA_FalconXUSDC/USDC | 7.87 m USDC | 89.1% | 10.9% | 856.69 k USDC | yellow | yellow | 8 |
| weETH/PYUSD | 14.60 m PYUSD | 88.2% | 11.8% | 1.73 m PYUSD | yellow | yellow | 4 |
| wstETH/WETH | 9.47 k WETH | 84.2% | 15.8% | 1.50 k WETH | yellow | yellow | 5 |
| wstETH/WETH | 28.47 k WETH | 83.7% | 16.3% | 4.64 k WETH | yellow | yellow | 5 |
| weETH/WETH | 5.03 k WETH | 82.7% | 17.3% | 870.06 WETH | yellow | yellow | 4 |
| stUSDS/USDC | 8.59 m USDC | 78.3% | 21.7% | 1.87 m USDC | yellow | red | 1 |
| wsrUSD/USDC | 10.14 m USDC | 76.3% | 23.7% | 2.40 m USDC | yellow | red | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 36.55 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 28.73 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 37.41 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDT Frontier (`0x79fd6400`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Frontier (`0x79fd6400`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 6.43 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDT (`0xa0804346`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDT (`0xa0804346`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 4.03 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Hakutora USDT (`0xa71d08a1`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Hakutora USDT (`0xa71d08a1`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 5.32 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Yearn USDT (`0x0963232e`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Yearn USDT (`0x0963232e`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 2.95 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDT (`0xa0804346`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDT (`0xa0804346`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 5.02 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Safe x Steakhouse USDT (`0xbeef47b9`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Safe x Steakhouse USDT (`0xbeef47b9`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.93 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Yearn USDT (`0x0963232e`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Yearn USDT (`0x0963232e`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 2.44 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.31 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | red | 0.00 | revoke | guardian: revokePendingCap | 200.00 m USDT | red market: no cap increase |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 962.55 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Prime (`0x8cb36491`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.53 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDT Frontier (`0x79fd6400`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Gauntlet USDT Frontier (`0x79fd6400`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.36 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.12 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Safe x Steakhouse USDT (`0xbeef47b9`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Safe x Steakhouse USDT (`0xbeef47b9`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.01 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Safe x Smokehouse USDT (`0xbeef0c18`) | v1 | wstETH/USDT | red | 0.00 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Safe x Smokehouse USDT (`0xbeef0c18`) | v1 | wstETH/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 929.65 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Safe x Smokehouse USDT (`0xbeef0c18`) | v1 | WBTC/USDT | red | 0.00 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Safe x Smokehouse USDT (`0xbeef0c18`) | v1 | WBTC/USDT | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 459.81 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Hakutora USDT (`0xa71d08a1`) | v1 | WBTC/USDT | red | 0.01 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Hakutora USDT (`0xa71d08a1`) | v1 | WBTC/USDT | red | 0.01 | decrease cap | curator: submitCap (a decrease applies at once) | 160.65 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Hyperithm USDT Core (`0x888883f0`) | v1 | wstETH/USDT | red | 0.02 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Hyperithm USDT Core (`0x888883f0`) | v1 | wstETH/USDT | red | 0.02 | decrease cap | curator: submitCap (a decrease applies at once) | 63.94 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Hyperithm USDT Core (`0x888883f0`) | v1 | WBTC/USDT | red | 0.05 | deallocate | allocator: reallocate | 840.09 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Hyperithm USDT Core (`0x888883f0`) | v1 | WBTC/USDT | red | 0.05 | decrease cap | curator: submitCap (a decrease applies at once) | 18.16 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.05 | deallocate | allocator: reallocate | 115.04 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse USDT (`0xbeef047a`) | v1 | sUSDS/USDT | red | 0.05 | decrease cap | curator: submitCap (a decrease applies at once) | 3.82 m USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.11 | deallocate | allocator: reallocate | 75.72 k USDtb | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.11 | decrease cap | curator: submitCap (a decrease applies at once) | 789.90 k USDtb | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Zircuit Finance USDT on Etheruem (`0xb632d9b2`) | v1 | wstETH/USDT | red | 0.21 | deallocate | allocator: reallocate | 1.44 k USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Zircuit Finance USDT on Etheruem (`0xb632d9b2`) | v1 | wstETH/USDT | red | 0.21 | decrease cap | curator: submitCap (a decrease applies at once) | 6.78 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.26 | deallocate | allocator: reallocate | 115.04 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDT (`0xa0804346`) | v1 | sUSDS/USDT | red | 0.26 | decrease cap | curator: submitCap (a decrease applies at once) | 722.82 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.44 | deallocate | allocator: reallocate | 1.81 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.44 | decrease cap | curator: submitCap (a decrease applies at once) | 4.14 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Yearn USDT (`0x0963232e`) | v1 | sUSDS/USDT | red | 0.73 | deallocate | allocator: reallocate | 115.04 USDT | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Yearn USDT (`0x0963232e`) | v1 | sUSDS/USDT | red | 0.73 | decrease cap | curator: submitCap (a decrease applies at once) | 254.53 k USDT | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.99 | deallocate | allocator: reallocate | 3.28 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.99 | decrease cap | curator: submitCap (a decrease applies at once) | 3.30 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Sentora RLUSD (`0x71cb2f80`) | v1 | weETH/RLUSD | red | n/a | revoke | guardian: revokePendingCap | 75.00 m RLUSD | red market: no cap increase |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.53 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.87 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-apxUSD-18JUN2026/USDC | PT past maturity (2026-06-18): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit 5001908
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26283306
