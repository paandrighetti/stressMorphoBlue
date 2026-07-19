As of 2026-07-16 (state block 25,545,086), across 24 evaluated markets, the survival frontier, the largest 24-hour outflow a market absorbs from instantaneous liquidity plus stress-liquidatable recoveries, ranges from 1.0% (AA_FalconXUSDC/USDC) to 41.1% (PT-reUSD-25JUN2026/USDC), median 10.7%. The binding variable is utilisation, not collateral class.

The second axis is the mirror image: under a class-aware extreme scenario, 20 of 24 markets fail on liquidity while 0 fail on solvency; latent insolvency stays below 0.7% of supply everywhere. Position books are conservative; liabilities are not.

Versus v1.0: the earlier yellow/green tiering was an artefact of a structural double-count (recoveries in both numerator and netted outflows, correction C6) compounded by non-callable healthy debt counted as monetisable (C4). The v1.1 engine removes both and reports what remains: a liquidity question that rate-driven replenishment, not modelled in this version, answers in practice.
