| Event | On-chain Liquidity Coverage Ratio | alpha | Time-to-illiquid | Probability bad debt > 0 | Severity | Verdict |
|---|---|---|---|---|---|---|
| rsETH incident-inspired fixture (2026) | 0.26 (red) | 60% | 6.2h (red) | 0% (green) | **red** | **PASS** |
| USDC depeg (2023) | 0.28 (red) | 48% | 6.6h (red) | 0% (green) | **red** | **PASS** |
| Staked-Ether discount (2022) | 3.20 (green) | 5% | infinite (green) | 0% (green) | **green** | **FAIL** |

Aggregate: **2 of 3 events flagged** by the pre-specified criteria. Values are produced by `scripts/generate_backtest_table.py`, which runs the same engine and the same slippage curves as `notebooks/phase4_demo.py`. Severity labels are the engine's own, not editorial.
