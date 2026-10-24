# Morpho Blue liquidity sentinel, 2026-10-24

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 9, yellow 15, green 0); not evaluated: 2.
- Tier changes since the previous run: 6.
- Actions listed: 9, for 8 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.27 k USDC | 100.0% | 0.0% | 0.00 USDC | red | red | 5 |
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | red | 2 |
| sUSDat/AUSD | 199.98 k AUSD | 96.8% | 3.2% | 6.31 k AUSD | red | red | 3 |
| PT-apyUSD-18JUN2026/USDC | 3.61 m USDC | 91.3% | 8.7% | 312.86 k USDC | red | yellow | 1 |
| sUSDe/USDtb | 976.72 k USDtb | 92.4% | 8.7% | 84.85 k USDtb | red | red | 2 |
| stUSDS/USDC | 7.52 m USDC | 91.0% | 9.0% | 673.77 k USDC | red | red | 3 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.1% | 9.9% | 166.37 k PYUSD | red | red | 5 |
| cbBTC/USDC | 343.22 m USDC | 90.1% | 9.9% | 34.03 m USDC | red | red | 5 |
| WBTC/USDC | 128.41 m USDC | 90.1% | 9.9% | 12.78 m USDC | red | red | 5 |
| wstETH/USDC | 33.01 m USDC | 89.9% | 10.1% | 3.34 m USDC | yellow | red | 1 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.6% | 10.4% | 246.49 PYUSD | yellow | yellow | 5 |
| sUSDe/PYUSD | 109.59 m PYUSD | 89.1% | 10.9% | 11.99 m PYUSD | yellow | yellow | 5 |
| weETH/RLUSD | 100.52 m RLUSD | 88.1% | 11.9% | 11.92 m RLUSD | yellow | yellow | 5 |
| mF-ONE/USDC | 23.24 m USDC | 87.6% | 12.4% | 2.89 m USDC | yellow | yellow | 5 |
| AA_FalconXUSDC/USDC | 8.00 m USDC | 87.5% | 12.5% | 997.96 k USDC | yellow | yellow | 5 |
| syrupUSDC/RLUSD | 902.19 k RLUSD | 86.1% | 13.9% | 125.11 k RLUSD | yellow | yellow | 5 |
| wsrUSD/USDC | 8.95 m USDC | 85.9% | 14.1% | 1.26 m USDC | yellow | yellow | 5 |
| weETH/PYUSD | 15.67 m PYUSD | 85.4% | 14.6% | 2.29 m PYUSD | yellow | red | 1 |
| wstETH/USDT | 162.66 m USDT | 84.6% | 15.4% | 25.11 m USDT | yellow | red | 1 |
| WBTC/USDT | 98.44 m USDT | 84.5% | 15.5% | 15.22 m USDT | yellow | red | 1 |
| wstETH/WETH | 9.10 k WETH | 83.7% | 16.3% | 1.49 k WETH | yellow | yellow | 2 |
| wstETH/WETH | 28.32 k WETH | 83.5% | 16.5% | 4.68 k WETH | yellow | yellow | 2 |
| sUSDS/USDT | 13.59 m USDT | 84.6% | 16.7% | 2.27 m USDT | yellow | yellow | 2 |
| weETH/WETH | 5.36 k WETH | 82.4% | 17.6% | 940.85 WETH | yellow | green | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| AlphaPing PT Frontier (`0x6701957a`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 1.91 k USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Mprinter USDC Yield Vault (`0x6fd59570`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.00 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Stake DAO USDC v1 (`0x13aa4f80`) | v1 | PT-reUSD-25JUN2026/USDC | red | 0.00 | decrease cap | curator: submitCap (a decrease applies at once) | 0.08 USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | deallocate | allocator: reallocate | 73.82 k USDtb | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Steakhouse Ethena USDtb (`0xbeefc1cd`) | v1 | sUSDe/USDtb | red | 0.10 | decrease cap | curator: submitCap (a decrease applies at once) | 829.43 k USDtb | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.30 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.92 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 11.87 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26261467
