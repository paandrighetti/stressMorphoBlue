### Results (engine v1.1)

**11 of 26 monitored markets evaluated** (engine v1.1; exclusions documented below). Survival frontier alpha\*: median 10.9%, minimum 9.8%. Tiers on alpha\*: 7 red, 4 yellow, 0 green. Under the extreme scenario, **11 of 11 markets fail the liquidity leg while 0 fail the solvency leg**: at target utilisation, 24-hour risk on Morpho Blue is a liability-liquidity question, not an asset-solvency one.

#### Base 24h stress, sorted by survival frontier

| Market | Supply | U | alpha (window) | alpha\* | TTI | P(insolv) | Tier |
|---|---|---|---|---|---|---|---|
| weETH/PYUSD | $52.1M | 90% | 41% | **9.8%** | 5.7h | 0% | red |
| weETH/RLUSD | $67.3M | 90% | 41% | **9.8%** | 5.8h | 0% | red |
| wstETH/USDC | $30.7M | 90% | 40% | **9.9%** | 5.9h | 0% | red |
| cbBTC/USDC | $287.6M | 90% | 38% | **10.2%** | 6.4h | 0% | red |
| WBTC/USDC | $115.8M | 90% | 38% | **10.2%** | 6.4h | 0% | red |
| wstETH/USDT | $172.7M | 89% | 40% | **10.9%** | 6.5h | 0% | red |
| wstETH/WETH | 11,554 WETH | 89% | 5% | **11.2%** | inf | 0% | yellow |
| wstETH/WETH | 48,995 WETH | 89% | 5% | **11.3%** | inf | 0% | yellow |
| weETH/WETH | 8,901 WETH | 89% | 5% | **11.4%** | inf | 0% | yellow |
| WBTC/USDT | $57.1M | 88% | 38% | **11.9%** | 7.5h | 0% | red |
| cbBTC/PYUSD | $2.8M | 78% | 7% | **21.8%** | inf | 0% | yellow |

alpha\* = stressed liquid stock / supply: the largest 24h outflow fraction the market absorbs (oracle at the window-worst price, recoveries from stress-liquidatable positions included, keeper executability enforced). Tier thresholds anchor to the framework's documented alpha calibration band: red < 10%, yellow < 30%, green >= 30%.

#### Extreme scenario (class-aware drawdown, 35% outflows)

| Market | dd applied | LSR (alpha=35%) | Latent insolvency | Illiquidity leg | Solvency leg |
|---|---|---|---|---|---|
| weETH/PYUSD | 25% | 0.28 | 0.02% | FAIL | pass |
| weETH/RLUSD | 25% | 0.28 | 0.11% | FAIL | pass |
| wstETH/USDC | 25% | 0.28 | 0.00% | FAIL | pass |
| cbBTC/USDC | 25% | 0.29 | 0.02% | FAIL | pass |
| WBTC/USDC | 25% | 0.29 | 0.14% | FAIL | pass |
| wstETH/USDT | 25% | 0.31 | 0.00% | FAIL | pass |
| wstETH/WETH | 5% | 0.32 | 0.01% | FAIL | pass |
| wstETH/WETH | 5% | 0.32 | 0.39% | FAIL | pass |
| weETH/WETH | 5% | 0.33 | 0.01% | FAIL | pass |
| WBTC/USDT | 25% | 0.34 | 0.69% | FAIL | pass |
| cbBTC/PYUSD | 25% | 0.62 | 0.11% | FAIL | pass |

Latent insolvency = debt not covered by collateral on stressed oracle terms (Morpho.sol exhaustion condition), independent of keeper execution.

#### Documented exclusions

* **sUSDe/PYUSD**: no slippage curve (no quotes)
* **sUSDS/USDT**: no slippage curve (no quotes)
* **sUSDe/USDtb**: no slippage curve (no quotes)
* **wsrUSD/USDC**: no slippage curve (no quotes)
* **AA_FalconXUSDC/USDC**: no slippage curve (no quotes)
* **syrupUSDC/RLUSD**: no slippage curve (no quotes)
* **PT-apyUSD-18JUN2026/USDC**: no slippage curve (no quotes)
* **LBTC/PYUSD**: no slippage curve (no quotes)
* **msY/USDC**: no oracle price series (oracle interface not supported this window)
* **PT-apxUSD-18JUN2026/USDC**: no slippage curve (no quotes)
* **stcUSD/USDT**: no slippage curve (no quotes)
* **sUSDat/AUSD**: no slippage curve (no quotes)
* **stUSDS/USDC**: no slippage curve (no quotes)
* **PT-reUSD-25JUN2026/USDC**: no slippage curve (no quotes)
* **mF-ONE/USDC**: no slippage curve (no quotes)
