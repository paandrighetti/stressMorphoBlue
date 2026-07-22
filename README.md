# Morpho Blue: Liquidity Stress Testing Framework

> A liquidity stress testing framework for Morpho Blue isolated
> lending markets and MetaMorpho vaults, adapted from Basel III
> regulatory standards (specifically the Liquidity Coverage Ratio of
> document BCBS 238, 2013).

**Status**: v1.1 engine (contract-faithful liquidation accounting, IRM accrual, single-counted LSR-24; corrections catalogued in [docs/MODEL_CORRECTIONS.md](./docs/MODEL_CORRECTIONS.md)). Automated tests run through GitHub Actions. Headline figures are generated from `docs/evaluation_results.csv` by `scripts/generate_report_tables.py` and injected by `scripts/assemble_docs.py`, never hand-transcribed. Not a production risk system. Not investment advice.

---

## A note on terminology

Every specialised term used in this repository is defined in
[`docs/GLOSSARY.md`](./docs/GLOSSARY.md). Mathematical symbols are
introduced with their units. Abbreviations are spelled out on first
use, with the abbreviation in parentheses. Documentation files do not
assume reader familiarity with either institutional finance or
decentralised-finance jargon.

---

## Motivation

Decentralised-finance lending pools have been shown to exhibit
inherent fragility under stress (Chiu, Ozdenoren, Yuan & Zhang, *On
the inherent fragility of decentralised-finance lending*, Bank for
International Settlements Working Paper 1062, 2023). Yet most public
risk reports for these pools transpose Basel concepts informally,
without explicit pass-or-fail criteria, and without a reproducible
backtest against historical events.

This project formalises the transposition for Morpho Blue, a
non-custodial lending protocol with isolated lending markets and
immutable parameters. It contributes:

1. An explicit on-chain analogue of the **Liquidity Coverage Ratio**
   (the regulatory ratio defined by the Basel Committee on Banking
   Supervision in document BCBS 238, 2013), with stated mapping
   limitations;

2. A **MetaMorpho vault curator discipline score**, the TVL-weighted
   exposure of each vault to the framework's severity tiers (red /
   yellow / green-watch / green-strong). The lower the score, the
   more conservative the vault. Implementation in
   `scripts/fetch_metamorpho_vaults.py`.

3. A **decoupled stress scenario architecture** that separates price
   stress (BCBS 238 24h LCR with class-floored drawdowns) from
   liquidity stress (amplified runoff alpha) rather than cumulating
   both into a single scenario, and an **extreme stress test**
   (drawdown 25%, alpha 35%) calibrated on the worst observed DeFi
   stress events to probe protocol behaviour beyond the empirical
   distribution.

The work is calibrated on the KelpDAO collateral exploit of April
2026 as a primary stress anchor, alongside the USDC depeg of March
2023 and the staked-Ether discount episode of May 2022.

---

## Repository structure

```
morpho-blue-liquidity-stress/
├── docs/
│   ├── GLOSSARY.md          # Definitions of all specialised terms
│   ├── METHODOLOGY.md       # Core methodological note
│   ├── SCENARIOS.md         # Stress-scenario specification
│   ├── DATA.md              # Data architecture
│   ├── BACKTEST.md          # Backtest specification
│   ├── REPORT.md            # Public writeup (Mirror.xyz-ready)
│   ├── BENCHMARK.md         # Comparison vs LlamaRisk / Block Analitica / Gauntlet / ChaosLabs
│   └── references.md        # Annotated bibliography
├── src/                     # Python implementation
├── data/                    # Local Parquet cache (gitignored) and event fixtures
├── notebooks/               # Reproducible analyses
├── scripts/                 # Data-acquisition + analysis entry points
│   ├── select_markets.py            # Top N markets by TVL
│   ├── fetch_markets.py             # Market metadata
│   ├── fetch_market_state.py        # On-chain state snapshots
│   ├── fetch_oracle_prices.py       # Oracle price history
│   ├── fetch_events.py              # Borrow/Repay/Supply/Withdraw/Liquidate events
│   ├── fetch_uniswap_quotes.py      # DEX slippage curves
│   ├── fetch_tvl.py                 # Aggregate TVL
│   ├── enrich_positions.py          # Reconstruct positions from events
│   ├── enrich_forward_looking.py    # Build profiles + run evaluation
│   ├── fetch_metamorpho_vaults.py   # MetaMorpho vault curator discipline
│   └── diagnose_corner_cases.py     # Investigate edge-case markets
├── tests/                   # pytest suite
└── README.md
```

---

## Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| **0** | Methodological note (`docs/METHODOLOGY.md`) | Done, version 0.3 |
| **1** | Stress-scenario formalisation (`docs/SCENARIOS.md`) | Done, version 0.2 |
| **2** | Data-acquisition architecture (`docs/DATA.md`), storage layer, tests, and live fetchers | Done, pipeline operational on 26 markets |
| **3** | Modelling: AdaptiveCurveIRM, slippage curve, S1 (withdrawal run), liquidation engine | Done |
| **3.5** | AdaptiveCurveIRM full-adaptive layer, geometric Time-Weighted Average Price oracle, S3 (oracle deviation), Monte Carlo, property-based tests | Done |
| **4** | Historical-backtest framework (`docs/BACKTEST.md`) and three event fixtures | Done, three of three events processed |
| **5** | Version-0.3 framework, decoupled stress scenarios (price-stress and liquidity-stress), continuous LCR criterion, Beta-scaled position distribution, asset-class slippage and drawdown calibration, extreme stress test, forward-looking analysis on 26 live markets (superseded by v1.1; see docs/MODEL_CORRECTIONS.md) | Done |
| **6** | v1.1: contract-faithful engine (C1-C7), live-position evaluation via the Morpho API, keyless multi-venue depth (Uniswap quoter, CoW Protocol, KyberSwap, Pendle router), survival-frontier panorama, generated-figures publication chain | Done |
| **6** | Public deliverables (Dune dashboard, Mirror article, public-facing summary) | Done |
| **7** | Empirical position-level reconstruction (`scripts/enrich_positions.py`), MetaMorpho vault curator discipline score (`scripts/fetch_metamorpho_vaults.py`), corner case diagnostic (`scripts/diagnose_corner_cases.py`), multi-day NSFR-style horizon (`--horizon-days N`), benchmark vs incumbent frameworks (`docs/BENCHMARK.md`) | Done |

---

## Headline findings

The framework monitors **26 Morpho Blue isolated markets** on Ethereum
mainnet; evaluated coverage and headline figures are generated from
`docs/evaluation_results.csv`, never hand-transcribed.

<!-- BEGIN GENERATED: readme_block -->
**Snapshot**: 2026-07-16, state block 25,545,086. **Under LCR-inspired 24-hour stress (LSR-24; engine v1.1)**: 24 of 26 monitored markets evaluated. Survival frontier alpha\* (max absorbable 24h outflow): median 10.7%, minimum 1.0%; tiers 9 red, 14 yellow, 1 green. Extreme scenario: 20/24 fail on liquidity, 0/24 on solvency. Full tables in docs/REPORT.md; corrections vs v1.0 in docs/MODEL_CORRECTIONS.md.
<!-- END GENERATED: readme_block -->

## Quick start

```bash
# Install (using uv, the recommended Python package manager)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the test suite
PYTHONPATH=src pytest tests/ -v

# Run the Phase-5 end-to-end demonstration
PYTHONPATH=src python notebooks/phase5_demo.py

# Set up local configuration (for Phase-2 data acquisition, when fetchers are implemented)
cp config.yaml config.local.yaml  # then edit to add secrets via environment variables
```

---

## How to read this repository (for reviewers and prospective employers)

If you have **5 minutes**: read [`docs/REPORT.md`](./docs/REPORT.md)
sections 1, 4, and 5. That is the framework's headline finding, the
forward-looking ranking, and the explicit limitations.

If you have **30 minutes**: read [`docs/REPORT.md`](./docs/REPORT.md)
end-to-end, then skim the bibliography in
[`docs/references.md`](./docs/references.md) and the glossary in
[`docs/GLOSSARY.md`](./docs/GLOSSARY.md) to assess academic grounding.

If you have **2 hours**: clone the repository, run the test suite,
and reproduce the Phase-5 demonstration. Inspect the v0.3 Liquidity
Coverage Ratio implementation in
`src/morpho_stress/backtest/liquidity_metrics.py` and the
event-calibrated outflow fraction.

---

## Methodological positioning

| Reference | Approach | Our positioning |
|---|---|---|
| Gauntlet, ChaosLabs | Agent-based simulation of liquidations | We use deterministic stress shocks at empirical quantiles plus a Monte Carlo layer; explicitly acknowledged simpler than agent-based; targeted as a future extension. |
| LlamaRisk, Block Analitica | Descriptive risk reports per market | We provide an explicit Basel-III mapping and a falsifiable hypothesis structure that they do not. |
| Chiu, Ozdenoren, Yuan, Zhang (BIS Working Paper 1062, 2023) | Theoretical model of decentralised-finance run dynamics | We are empirical and applied; their model justifies our framework's relevance, but our work is implementation-oriented. |
| Steakhouse Financial | Vault-curator-centric reporting | Our secondary hypothesis explicitly targets curator risk discipline as a quantifiable gap, a question they engage with operationally but do not formalise. |

---

## Links

- **Live Dune dashboard** (TVL, top markets, liquidation flows): https://dune.com/bandulf/morpho-blue-liquidity-stress
- **Published article**: [`MIRROR_ARTICLE.md`](./MIRROR_ARTICLE.md)

---

## Citing this work

If this framework informs your research or analysis, please cite:

> Pierre-Antoine Andrighetti. (2026). *Morpho Blue: a Basel III liquidity stress testing framework for isolated lending markets and MetaMorpho vaults.* https://github.com/paandrighetti/stressMorphoBlue

---

## Contact

https://www.linkedin.com/in/pierre-antoine-andrighetti
https://x.com/bandulf
p.a.andrighetti@gmail.com

---

## License

MIT. See [LICENSE](./LICENSE).

## Disclaimer

This work is academic and exploratory. It is not investment advice;
not a recommendation to deposit on or borrow from any Morpho Blue
lending market; not a substitute for a security audit or formal risk
assessment. The author has no affiliation with Morpho Labs,
MetaMorpho vault curators, or any protocol mentioned, beyond public
usage.
