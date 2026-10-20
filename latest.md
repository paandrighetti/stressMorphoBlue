# Morpho Blue liquidity sentinel, 2026-10-20

Read-only. Each day the stressMorphoBlue engine re-evaluates the roster's markets on live data, and the rule of [docs/SENTINEL.md](https://github.com/paandrighetti/stressMorphoBlue/blob/main/docs/SENTINEL.md) lists the actions a vault's sentinel (Vault V2) or guardian, curator and allocator (MetaMorpho) could take. No transaction is signed. Not investment advice.

## Summary

- Markets evaluated: 24 (red 7, yellow 15, green 2); not evaluated: 2.
- Tier changes since the previous run: 0.
- Actions listed: 0, for 0 vaults.
- Vault data: v1 failed: Client error '400 Bad Request' for url 'https://api.morpho.org/graphql'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400; Vault V2 not covered yet (fields of VaultV2: adapters, address, allocators, apy, asset, avgNetApy, avgNetApyExcludingRewards, caps, chain, creationBlockNumber, creationTimestamp, curator, curators, factory, forceDeallocatableLiquidity, forceDeallocatableLiquidityUsd, gatesConfig, historicalState, id, idleAssets, idleAssetsUsd, liquidity, liquidityAdapter, liquidityData, liquidityUsd, listed, listingHistory, managementFee, managementFeeConfig, managementFeeRecipient, managementFeeRecipientConfig, maxApy, maxRate, metadata, name, netApy, netApyExcludingRewards, owner, pendingConfigs, performanceFee, performanceFeeConfig, performanceFeeRecipient, performanceFeeRecipientConfig, positions, rewards, sentinels, sharePrice, symbol, timelocks, totalAssets, totalAssetsUsd, totalSupply, type, warnings)

## Markets

alpha* is the largest share of supply the market can pay out within 24 hours under the stress (red below 10%, yellow below 30%). Absorbable is alpha* times supply.

| Market | Supply | Utilization | alpha* | Absorbable in 24 h | Tier | Previous run | Runs in tier |
|---|---|---|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | 2.47 k USDC | 91.9% | 8.1% | 200.00 USDC | red | none | 1 |
| weETH/PYUSD | 29.87 m PYUSD | 90.2% | 9.8% | 2.91 m PYUSD | red | none | 1 |
| cbBTC/USDC | 343.42 m USDC | 90.1% | 9.9% | 34.00 m USDC | red | none | 1 |
| wstETH/USDC | 32.55 m USDC | 90.1% | 9.9% | 3.22 m USDC | red | none | 1 |
| cbBTC/PYUSD | 1.69 m PYUSD | 90.1% | 9.9% | 168.21 k PYUSD | red | none | 1 |
| WBTC/USDC | 130.09 m USDC | 90.1% | 9.9% | 12.93 m USDC | red | none | 1 |
| PT-apyUSD-18JUN2026/USDC | 3.65 m USDC | 90.1% | 9.9% | 363.44 k USDC | red | none | 1 |
| mF-ONE/USDC | 24.84 m USDC | 89.3% | 10.7% | 2.67 m USDC | yellow | none | 1 |
| LBTC/PYUSD | 2.39 k PYUSD | 89.2% | 10.8% | 257.18 PYUSD | yellow | none | 1 |
| stUSDS/USDC | 7.64 m USDC | 89.1% | 10.9% | 832.55 k USDC | yellow | none | 1 |
| sUSDe/PYUSD | 109.57 m PYUSD | 89.0% | 11.0% | 12.08 m PYUSD | yellow | none | 1 |
| sUSDe/USDtb | 1.02 m USDtb | 88.6% | 12.4% | 126.61 k USDtb | yellow | none | 1 |
| weETH/RLUSD | 101.96 m RLUSD | 87.2% | 12.8% | 13.10 m RLUSD | yellow | none | 1 |
| wstETH/WETH | 36.25 k WETH | 86.9% | 13.1% | 4.75 k WETH | yellow | none | 1 |
| AA_FalconXUSDC/USDC | 8.12 m USDC | 86.3% | 13.7% | 1.11 m USDC | yellow | none | 1 |
| wstETH/WETH | 9.28 k WETH | 85.8% | 14.2% | 1.32 k WETH | yellow | none | 1 |
| wstETH/USDT | 153.77 m USDT | 85.1% | 14.9% | 22.89 m USDT | yellow | none | 1 |
| WBTC/USDT | 94.37 m USDT | 85.1% | 14.9% | 14.08 m USDT | yellow | none | 1 |
| sUSDS/USDT | 13.58 m USDT | 85.3% | 16.0% | 2.18 m USDT | yellow | none | 1 |
| weETH/WETH | 5.89 k WETH | 83.8% | 16.2% | 955.89 WETH | yellow | none | 1 |
| wsrUSD/USDC | 9.15 m USDC | 82.7% | 17.3% | 1.58 m USDC | yellow | none | 1 |
| syrupUSDC/RLUSD | 1.21 m RLUSD | 81.2% | 18.8% | 227.11 k RLUSD | yellow | none | 1 |
| sUSDat/AUSD | 285.19 k AUSD | 64.9% | 35.1% | 100.22 k AUSD | green | none | 1 |
| stcUSD/USDT | 17.41 USDT | 7.4% | 92.6% | 16.12 USDT | green | none | 1 |

## Actions by vault

None today.

## Not evaluated today

| Market | Reason |
|---|---|
| msY/USDC | no oracle price series (oracle interface not supported this window) |
| PT-apxUSD-18JUN2026/USDC | PT past maturity (2026-06-18): exit is par redemption, AMM depth not applicable |

## Inputs

- Engine: stressMorphoBlue v1.1, methodology rolling-window-v2, commit c9dd582
- Ethereum endpoint: public endpoint https://eth.drpc.org
- Position book and vaults: Morpho API (https://api.morpho.org/graphql)
- Evaluation block: 26235746
