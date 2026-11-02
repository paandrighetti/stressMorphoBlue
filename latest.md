# Morpho Blue liquidity sentinel, 2026-11-02

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 11, yellow 12, green 1); not evaluated: 2.
- Tier changes since the previous run: 7.
- Actions listed: 10, for 7 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| sUSDat/AUSD | 210.30 k AUSD | 92.4% | 7.6% | 15.95 k AUSD | red | red | 4 |
| PT-apyUSD-18JUN2026/USDC | 3.58 m USDC | 92.3% | 7.7% | 274.94 k USDC | red | red | 4 |
| wsrUSD/USDC | 7.30 m USDC | 90.9% | 9.1% | 661.18 k USDC | red | yellow | 1 |
| mF-ONE/USDC | 23.10 m USDC | 90.7% | 9.3% | 2.15 m USDC | red | red | 4 |
| wstETH/WETH | 8.38 k WETH | 90.7% | 9.3% | 779.98 WETH | red | red | 4 |
| wstETH/WETH | 32.45 k WETH | 90.6% | 9.4% | 3.05 k WETH | red | yellow | 1 |
| stUSDS/USDC | 6.13 m USDC | 90.6% | 9.4% | 576.80 k USDC | red | red | 2 |
| weETH/PYUSD | 14.47 m PYUSD | 90.5% | 9.5% | 1.38 m PYUSD | red | red | 4 |
| LBTC/PYUSD | 1.29 k PYUSD | 90.0% | 10.0% | 127.94 PYUSD | red | red | 4 |
| cbBTC/PYUSD | 1.67 m PYUSD | 90.0% | 10.0% | 166.26 k PYUSD | red | red | 13 |
| stcUSD/USDT | 2.41 USDT | 90.0% | 10.0% | 0.24 USDT | red | red | 10 |
| weETH/WETH | 4.17 k WETH | 88.9% | 11.1% | 461.63 WETH | yellow | red | 1 |
| sUSDe/USDtb | 901.91 k USDtb | 88.6% | 11.4% | 102.98 k USDtb | yellow | yellow | 2 |
| sUSDe/PYUSD | 115.00 m PYUSD | 88.2% | 11.8% | 13.55 m PYUSD | yellow | yellow | 3 |
| weETH/RLUSD | 78.13 m RLUSD | 87.3% | 12.7% | 9.93 m RLUSD | yellow | yellow | 4 |
| cbBTC/USDC | 244.65 m USDC | 86.9% | 13.1% | 32.00 m USDC | yellow | red | 1 |
| wstETH/USDC | 34.96 m USDC | 86.8% | 13.2% | 4.61 m USDC | yellow | red | 1 |
| WBTC/USDC | 141.63 m USDC | 86.4% | 13.6% | 19.24 m USDC | yellow | red | 1 |
| AA_FalconXUSDC/USDC | 8.17 m USDC | 85.9% | 14.1% | 1.15 m USDC | yellow | red | 1 |
| wstETH/USDT | 127.51 m USDT | 82.0% | 18.0% | 22.92 m USDT | yellow | yellow | 3 |
| WBTC/USDT | 106.10 m USDT | 82.0% | 18.0% | 19.10 m USDT | yellow | yellow | 3 |
| syrupUSDC/RLUSD | 229.06 k RLUSD | 81.2% | 18.8% | 43.01 k RLUSD | yellow | yellow | 3 |
| sUSDS/USDT | 5.66 m USDT | 81.8% | 22.7% | 1.28 m USDT | yellow | yellow | 3 |
| PT-apxUSD-18JUN2026/USDC | 1.71 k USDC | 0.1% | 99.9% | 1.70 k USDC | green | none | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.37 | deallocate | allocator: reallocate | 779.98 WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse ETH (`0xbeef050e`) | v1 | wstETH/WETH | red | 0.37 | decrease cap | curator: submitCap (a decrease applies at once) | 2.12 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.60 | deallocate | allocator: reallocate | 2.15 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Smokehouse USDC (`0xbeefff20`) | v1 | mF-ONE/USDC | red | 0.60 | decrease cap | curator: submitCap (a decrease applies at once) | 3.61 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.69 | deallocate | allocator: reallocate | 3.05 k WETH | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Vault Bridge WETH (`0x31a56849`) | v1 | wstETH/WETH | red | 0.69 | decrease cap | curator: submitCap (a decrease applies at once) | 4.44 k WETH | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.50 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.64 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 15.83 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26327255
