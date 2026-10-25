# Morpho Blue liquidity sentinel, 2026-10-25

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 7, yellow 17, green 0); not evaluated: 2.
- Tier changes since the previous run: 6.
- Actions listed: 6, for 5 vaults.
- Vault data: MetaMorpho V1: 162 vaults allocated to the roster (fields supplyAssets, supplyCap, pendingSupplyCap); Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| stcUSD/USDT | 2.41 USDT | 100.0% | 0.0% | 0.00 USDT | red | red | 3 |
| sUSDat/AUSD | 200.44 k AUSD | 96.7% | 3.3% | 6.65 k AUSD | red | red | 4 |
| PT-apyUSD-18JUN2026/USDC | 3.61 m USDC | 91.2% | 8.8% | 318.27 k USDC | red | red | 2 |
| wsrUSD/USDC | 8.68 m USDC | 90.1% | 9.9% | 856.53 k USDC | red | yellow | 1 |
| cbBTC/PYUSD | 1.68 m PYUSD | 90.1% | 9.9% | 166.21 k PYUSD | red | red | 6 |
| wstETH/USDC | 32.90 m USDC | 90.1% | 9.9% | 3.26 m USDC | red | yellow | 1 |
| cbBTC/USDC | 343.17 m USDC | 90.1% | 9.9% | 34.04 m USDC | red | red | 6 |
| WBTC/USDC | 128.97 m USDC | 89.7% | 10.3% | 13.28 m USDC | yellow | red | 1 |
| LBTC/PYUSD | 2.38 k PYUSD | 89.7% | 10.3% | 244.87 PYUSD | yellow | yellow | 6 |
| stUSDS/USDC | 7.50 m USDC | 89.6% | 10.4% | 781.84 k USDC | yellow | red | 1 |
| sUSDe/PYUSD | 109.59 m PYUSD | 89.1% | 10.9% | 11.99 m PYUSD | yellow | yellow | 6 |
| sUSDe/USDtb | 1.01 m USDtb | 89.1% | 12.0% | 121.99 k USDtb | yellow | red | 1 |
| weETH/RLUSD | 100.53 m RLUSD | 87.9% | 12.1% | 12.20 m RLUSD | yellow | yellow | 6 |
| AA_FalconXUSDC/USDC | 8.01 m USDC | 87.5% | 12.5% | 1.00 m USDC | yellow | yellow | 6 |
| mF-ONE/USDC | 23.39 m USDC | 87.0% | 13.0% | 3.04 m USDC | yellow | yellow | 6 |
| weETH/PYUSD | 15.45 m PYUSD | 86.1% | 13.9% | 2.14 m PYUSD | yellow | yellow | 2 |
| syrupUSDC/RLUSD | 902.27 k RLUSD | 86.1% | 13.9% | 125.11 k RLUSD | yellow | yellow | 6 |
| wstETH/USDT | 162.08 m USDT | 85.0% | 15.0% | 24.36 m USDT | yellow | yellow | 2 |
| WBTC/USDT | 98.73 m USDT | 84.9% | 15.1% | 14.87 m USDT | yellow | yellow | 2 |
| wstETH/WETH | 9.04 k WETH | 84.3% | 15.7% | 1.42 k WETH | yellow | yellow | 3 |
| wstETH/WETH | 28.32 k WETH | 84.1% | 15.9% | 4.50 k WETH | yellow | yellow | 3 |
| sUSDS/USDT | 13.52 m USDT | 85.0% | 16.3% | 2.21 m USDT | yellow | yellow | 3 |
| weETH/WETH | 5.26 k WETH | 82.5% | 17.5% | 919.27 WETH | yellow | yellow | 2 |
| PT-reUSD-25JUN2026/USDC | 3.10 k USDC | 73.2% | 26.8% | 829.90 USDC | yellow | red | 1 |

## Actions by vault

Coverage is the market's absorbable outflow over the vault's allocation: below 1, the vault could not withdraw all of it within 24 hours even if it were first in line.

| Vault | Version | Market | Tier | Coverage | Action | Role and call | Amount | Why |
|---|---|---|---|---|---|---|---|---|
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.84 | deallocate | allocator: reallocate | 3.26 m USDC | red market and the vault could not exit within 24 hours: withdraw what the market's idle liquidity allows |
| Spark Blue Chip USDC Vault (`0x56a76b42`) | v1 | wstETH/USDC | red | 0.84 | decrease cap | curator: submitCap (a decrease applies at once) | 3.90 m USDC | red market and the vault could not exit within 24 hours: cap set to the current allocation |
| Gauntlet USDC RWA (`0xa8875aae`) | v1 | AA_FalconXUSDC/USDC | yellow | 0.30 | revoke | guardian: revokePendingCap | 40.00 m USDC | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Gauntlet WETH Prime (`0x2371e134`) | v1 | weETH/WETH | yellow | 0.90 | revoke | guardian: revokePendingCap | 100.00 k WETH | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
| Vault Bridge USDT (`0xc54b4e08`) | v1 | WBTC/USDT | yellow | 11.54 | revoke | guardian: revokePendingCap | 200.00 m USDT | yellow market: the pending cap exceeds what the market absorbs in 24 hours |
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
- Evaluation block: 26268654
