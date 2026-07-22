### Results (engine v1.1)

**Snapshot**: 2026-07-16, state block 25,545,086. **24 of 26 monitored markets evaluated** (engine v1.1; exclusions documented below). Survival frontier alpha\*: median 10.7%, minimum 1.0%. Tiers on alpha\*: 9 red, 14 yellow, 1 green. Under the extreme scenario, **20 of 24 markets fail the liquidity leg while 0 fail the solvency leg**: at target utilisation, 24-hour risk on Morpho Blue is a liability-liquidity question, not an asset-solvency one.

#### Base 24h stress, sorted by survival frontier

| Market | Supply | U | alpha (window) | alpha\* | TTI | P(insolv) | Tier |
|---|---|---|---|---|---|---|---|
| AA_FalconXUSDC/USDC | $44.8M | 99% | 5% | **1.0%** | 4.9h | 0% | red |
| stcUSD/USDT | $1.4M | 93% | 5% | **7.1%** | inf | 0% | red |
| stUSDS/USDC | $16.7M | 91% | 5% | **9.0%** | inf | 0% | red |
| sUSDe/USDtb | $10.2M | 91% | 5% | **9.2%** | inf | 0% | red |
| mF-ONE/USDC | $16.3M | 90% | 5% | **9.8%** | inf | 0% | red |
| weETH/PYUSD | $52.1M | 90% | 41% | **9.8%** | 5.7h | 0% | red |
| wsrUSD/USDC | $17.8M | 90% | 5% | **9.8%** | inf | 0% | red |
| weETH/RLUSD | $67.3M | 90% | 41% | **9.8%** | 5.8h | 0% | red |
| wstETH/USDC | $30.7M | 90% | 40% | **9.9%** | 5.9h | 0% | red |
| cbBTC/USDC | $287.6M | 90% | 38% | **10.2%** | 6.4h | 0% | yellow |
| WBTC/USDC | $115.8M | 90% | 38% | **10.2%** | 6.4h | 0% | yellow |
| LBTC/PYUSD | $46.7M | 89% | 38% | **10.6%** | 6.7h | 0% | yellow |
| PT-apyUSD-18JUN2026/USDC | $3.2M | 89% | 46% | **10.8%** | 5.7h | 4% | yellow |
| syrupUSDC/RLUSD | $33.8M | 90% | 5% | **10.8%** | inf | 0% | yellow |
| wstETH/USDT | $172.7M | 89% | 40% | **10.9%** | 6.5h | 0% | yellow |
| sUSDe/PYUSD | $40.6M | 89% | 5% | **11.0%** | inf | 0% | yellow |
| wstETH/WETH | 11,554 WETH | 89% | 5% | **11.2%** | inf | 0% | yellow |
| wstETH/WETH | 48,995 WETH | 89% | 5% | **11.3%** | inf | 0% | yellow |
| weETH/WETH | 8,901 WETH | 89% | 5% | **11.4%** | inf | 0% | yellow |
| WBTC/USDT | $57.1M | 88% | 38% | **11.9%** | 7.5h | 0% | yellow |
| PT-apxUSD-18JUN2026/USDC | $212k | 86% | 46% | **13.7%** | 7.2h | 0% | yellow |
| cbBTC/PYUSD | $2.8M | 78% | 7% | **21.8%** | inf | 0% | yellow |
| sUSDat/AUSD | $8.9M | 75% | 41% | **24.8%** | 14.5h | 0% | yellow |
| PT-reUSD-25JUN2026/USDC | $640k | 59% | 5% | **41.1%** | inf | 0% | green |

alpha\* = stressed liquid stock / supply: the largest 24h outflow fraction the market absorbs (oracle at the window-worst price, recoveries from stress-liquidatable positions included, keeper executability enforced). Tier thresholds anchor to the framework's documented alpha calibration band: red < 10%, yellow < 30%, green >= 30%.

#### Extreme scenario (class-aware drawdown, 35% outflows)

| Market | dd applied | LSR (alpha=35%) | Latent insolvency | Illiquidity leg | Solvency leg |
|---|---|---|---|---|---|
| AA_FalconXUSDC/USDC | 5% | 0.03 | 0.00% | FAIL | pass |
| stcUSD/USDT | 5% | 2.86 | 0.00% | pass | pass |
| stUSDS/USDC | 5% | 1.35 | 0.00% | pass | pass |
| sUSDe/USDtb | 5% | 0.66 | 0.00% | FAIL | pass |
| mF-ONE/USDC | 5% | 0.28 | 0.00% | FAIL | pass |
| weETH/PYUSD | 25% | 0.28 | 0.02% | FAIL | pass |
| wsrUSD/USDC | 5% | 0.28 | 0.01% | FAIL | pass |
| weETH/RLUSD | 25% | 0.28 | 0.11% | FAIL | pass |
| wstETH/USDC | 25% | 0.28 | 0.00% | FAIL | pass |
| cbBTC/USDC | 25% | 0.29 | 0.02% | FAIL | pass |
| WBTC/USDC | 25% | 0.29 | 0.14% | FAIL | pass |
| LBTC/PYUSD | 25% | 0.32 | 0.00% | FAIL | pass |
| PT-apyUSD-18JUN2026/USDC | 25% | 0.31 | 0.25% | FAIL | pass |
| syrupUSDC/RLUSD | 5% | 0.84 | 0.00% | FAIL | pass |
| wstETH/USDT | 25% | 0.31 | 0.00% | FAIL | pass |
| sUSDe/PYUSD | 5% | 2.52 | 0.00% | pass | pass |
| wstETH/WETH | 5% | 0.32 | 0.01% | FAIL | pass |
| wstETH/WETH | 5% | 0.32 | 0.39% | FAIL | pass |
| weETH/WETH | 5% | 0.33 | 0.01% | FAIL | pass |
| WBTC/USDT | 25% | 0.34 | 0.69% | FAIL | pass |
| PT-apxUSD-18JUN2026/USDC | 25% | 0.39 | 0.00% | FAIL | pass |
| cbBTC/PYUSD | 25% | 0.62 | 0.11% | FAIL | pass |
| sUSDat/AUSD | 25% | 0.85 | 0.01% | FAIL | pass |
| PT-reUSD-25JUN2026/USDC | 5% | 1.18 | 0.00% | pass | pass |

Latent insolvency = debt not covered by collateral on stressed oracle terms (Morpho.sol exhaustion condition), independent of keeper execution.

#### Documented exclusions

* **sUSDS/USDT**: no slippage curve (unusable quotes (7/7 positive-bps rows))
* **msY/USDC**: no oracle price series (oracle interface not supported this window)
