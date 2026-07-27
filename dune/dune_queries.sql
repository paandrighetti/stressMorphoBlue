-- ============================================================================
-- Morpho Blue liquidity stress framework, Dune SQL queries
-- v1.1, 2026-07-27
-- Companion to github.com/paandrighetti/stressMorphoBlue
-- Dashboard: dune.com/bandulf/morpho-blue-liquidity-stress
-- ============================================================================
--
-- v1.1 change note. The v1.0 draft of Q4 summed raw `assets` across all
-- markets per flow type. Loan assets differ across markets (USDC has 6
-- decimals, WETH has 18) so that total mixed units and decimals in a single
-- number. v1.1 normalizes every amount by its token's decimals and never
-- aggregates across loan assets. This is the same defect class as the
-- mixed-unit supply share corrected in scripts/run_evaluation.py, and the
-- same rule applies here: no exchange rate, no cross-asset totals, ever.
--
-- SCOPE DECISION, read before adding any panel.
--
-- This dashboard does NOT reproduce the published analysis. The survival
-- frontier alpha* depends on measured exit depth from offchain aggregators,
-- fitted slippage curves and a 200-path Monte Carlo layer. None of that is
-- expressible in SQL. Any panel that appears to compute alpha* creates a
-- second source of truth that will diverge from docs/REPORT.md within days.
--
-- This dashboard also does NOT reconstruct outstanding balances. Morpho Blue
-- emits assets and shares on every flow event and interest accrues through
-- separate AccrueInterest events, so summing Supply minus Withdraw
-- understates the real position and the error grows with time and
-- utilization. Published balances come from onchain state reads at the
-- pinned block (docs/evaluation_manifest.json, block 25545086).
--
-- What this dashboard shows: the frozen publication table (uploaded dataset,
-- Q5) and discrete onchain events that Dune handles well (Q1 to Q4).
--
-- TABLE NAMING, verified convention:
--   morpho_blue_ethereum.morphoblue_evt_<eventname>   (all lowercase)
-- Events: supply, withdraw, borrow, repay, liquidate, supplycollateral,
--   withdrawcollateral, createmarket, accrueinterest.
-- Token metadata: tokens.erc20 (curated), filter blockchain = 'ethereum'.
-- There is no curated lending.* dataset for Morpho Blue.
--
-- COLUMN NAMES ARE NOT ASSUMED. Decoded tables keep the Solidity event
-- parameter names (camelCase). Run STEP 0 first, read the actual schema in
-- the output, and reconcile it with the queries below before running them.
--
-- ROSTER FILTER. Q2, Q3 and Q4 accept the 26 monitored market ids from
-- markets_top.yaml. Paste them as 0x... literals in the commented IN lists.
-- If the engine rejects a 0x literal against the id column, wrap each value
-- in from_hex('...') without the 0x prefix.
--
-- BACKLINKS. After saving each query on Dune, paste its URL
-- (dune.com/queries/NNNNNNN) on the matching line below and commit:
--   STEP 0 : <paste url>
--   Q1     : <paste url>
--   Q2     : <paste url>
--   Q3     : <paste url>
--   Q4     : <paste url>
--   Q5     : <paste url>
-- ============================================================================


-- ============================================================================
-- STEP 0, sanity check. Run this FIRST, on the DuneSQL engine.
-- ============================================================================
-- Rows returned      : namespace correct, read the column names, proceed.
-- "table not found"  : check the chain suffix and the engine dropdown.
-- 0 rows             : widen the window.
-- ============================================================================

SELECT *
FROM morpho_blue_ethereum.morphoblue_evt_createmarket
LIMIT 5;


-- ============================================================================
-- Q1, market registry with human-readable symbols.
-- ============================================================================
-- Morpho Blue markets are immutable once created: this is a reference table.
-- Use it to confirm the 26 monitored ids resolve to the parameters recorded
-- in markets_top.yaml. lltv is WAD-scaled, meaning an 18-decimal fixed-point
-- integer, hence the division by 1e18.
-- ============================================================================

WITH tok AS (
    SELECT contract_address, symbol, decimals
    FROM tokens.erc20
    WHERE blockchain = 'ethereum'
)
SELECT
    m.id                                   AS market_id,
    COALESCE(ct.symbol, 'unknown')         AS collateral,
    COALESCE(lt.symbol, 'unknown')         AS loan_asset,
    CAST(m.lltv AS double) / 1e18          AS liquidation_ltv,
    m.oracle,
    m.irm                                  AS interest_rate_model,
    m.evt_block_time                       AS created_at
FROM morpho_blue_ethereum.morphoblue_evt_createmarket m
LEFT JOIN tok lt ON lt.contract_address = m.loanToken
LEFT JOIN tok ct ON ct.contract_address = m.collateralToken
ORDER BY created_at DESC;


-- ============================================================================
-- Q2, liquidations on the monitored roster, decimal-normalized.
-- ============================================================================
-- The panel that justifies the dashboard. The published framework asserts
-- that no evaluated market fails the solvency leg and that keeper
-- rationality suppresses execution before bad debt is booked. Observed
-- liquidations, and above all a non-zero badDebtAssets, are the
-- falsification surface for that claim.
--
-- Units: repaid and bad debt are in the market's loan asset, seized is in
-- its collateral asset. Amounts are normalized per market and labelled; do
-- not sum any of these columns across markets with different assets.
-- ============================================================================

WITH tok AS (
    SELECT contract_address, symbol, decimals
    FROM tokens.erc20
    WHERE blockchain = 'ethereum'
),
lab AS (
    SELECT
        m.id,
        COALESCE(ct.symbol, 'unknown') || '/' ||
        COALESCE(lt.symbol, 'unknown')          AS market,
        lt.decimals                              AS loan_dec,
        ct.decimals                              AS coll_dec
    FROM morpho_blue_ethereum.morphoblue_evt_createmarket m
    LEFT JOIN tok lt ON lt.contract_address = m.loanToken
    LEFT JOIN tok ct ON ct.contract_address = m.collateralToken
)
SELECT
    date_trunc('day', l.evt_block_time)                          AS day,
    lab.market,
    COUNT(*)                                                     AS n_liquidations,
    COUNT(DISTINCT l.borrower)                                   AS n_borrowers,
    SUM(CAST(l.repaidAssets  AS double) / power(10, lab.loan_dec)) AS repaid_loan_units,
    SUM(CAST(l.seizedAssets  AS double) / power(10, lab.coll_dec)) AS seized_collateral_units,
    SUM(CAST(l.badDebtAssets AS double) / power(10, lab.loan_dec)) AS bad_debt_loan_units
FROM morpho_blue_ethereum.morphoblue_evt_liquidate l
JOIN lab ON lab.id = l.id
WHERE l.evt_block_time >= TIMESTAMP '2025-01-01 00:00:00'
  -- AND l.id IN (0x..., 0x...)   -- 26 monitored ids from markets_top.yaml
GROUP BY 1, 2
ORDER BY 1 DESC, bad_debt_loan_units DESC;


-- ============================================================================
-- Q3, borrower activity concentration by market.
-- ============================================================================
-- The stress engine reads the live position book and is sensitive to
-- concentration. This is a live proxy for that shape. Shares are ratios
-- within one market, so decimals cancel and no normalization is needed.
--
-- CAVEAT to state in the panel title: this counts addresses that borrowed
-- in the window, not current balances. Label it "activity proxy", never
-- "current borrowers".
-- ============================================================================

WITH tok AS (
    SELECT contract_address, symbol
    FROM tokens.erc20
    WHERE blockchain = 'ethereum'
),
lab AS (
    SELECT
        m.id,
        COALESCE(ct.symbol, 'unknown') || '/' ||
        COALESCE(lt.symbol, 'unknown') AS market
    FROM morpho_blue_ethereum.morphoblue_evt_createmarket m
    LEFT JOIN tok lt ON lt.contract_address = m.loanToken
    LEFT JOIN tok ct ON ct.contract_address = m.collateralToken
),
borrow_activity AS (
    SELECT id, onBehalf AS borrower, SUM(CAST(assets AS double)) AS borrowed_raw
    FROM morpho_blue_ethereum.morphoblue_evt_borrow
    WHERE evt_block_time >= TIMESTAMP '2026-01-01 00:00:00'
      -- AND id IN (0x..., 0x...)   -- 26 monitored ids
    GROUP BY 1, 2
),
ranked AS (
    SELECT
        id,
        borrowed_raw,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY borrowed_raw DESC) AS rk,
        SUM(borrowed_raw) OVER (PARTITION BY id)                       AS market_total
    FROM borrow_activity
)
SELECT
    lab.market,
    COUNT(*)                                                             AS n_active_borrowers,
    SUM(CASE WHEN rk <= 3  THEN borrowed_raw ELSE 0 END) / market_total  AS top3_share,
    SUM(CASE WHEN rk <= 10 THEN borrowed_raw ELSE 0 END) / market_total  AS top10_share
FROM ranked
JOIN lab ON lab.id = ranked.id
WHERE market_total > 0
GROUP BY lab.market, market_total
ORDER BY top3_share DESC;


-- ============================================================================
-- Q4, weekly gross flows, decimal-normalized, grouped by loan asset.
-- ============================================================================
-- Panel title must contain the word "flows", never "balances": interest
-- accrual is absent by construction, so cumulative net flow is not the
-- outstanding position.
--
-- Chart as one series per loan asset (stacked bars or a filterable table).
-- Never draw a single total line across assets: that would sum USDC with
-- WETH, which is the defect this v1.1 exists to remove.
-- ============================================================================

WITH tok AS (
    SELECT contract_address, symbol, decimals
    FROM tokens.erc20
    WHERE blockchain = 'ethereum'
),
lab AS (
    SELECT m.id, lt.symbol AS loan_asset, lt.decimals AS dec
    FROM morpho_blue_ethereum.morphoblue_evt_createmarket m
    JOIN tok lt ON lt.contract_address = m.loanToken
),
flows AS (
    SELECT evt_block_time, id, 'supply' AS flow_type,
           CAST(assets AS double) AS amt
    FROM morpho_blue_ethereum.morphoblue_evt_supply
    UNION ALL
    SELECT evt_block_time, id, 'withdraw', -CAST(assets AS double)
    FROM morpho_blue_ethereum.morphoblue_evt_withdraw
    UNION ALL
    SELECT evt_block_time, id, 'borrow', CAST(assets AS double)
    FROM morpho_blue_ethereum.morphoblue_evt_borrow
    UNION ALL
    SELECT evt_block_time, id, 'repay', -CAST(assets AS double)
    FROM morpho_blue_ethereum.morphoblue_evt_repay
)
SELECT
    date_trunc('week', f.evt_block_time)      AS week,
    lab.loan_asset,
    f.flow_type,
    SUM(f.amt / power(10, lab.dec))           AS amount_loan_units
FROM flows f
JOIN lab ON lab.id = f.id
WHERE f.evt_block_time >= TIMESTAMP '2026-01-01 00:00:00'
  -- AND f.id IN (0x..., 0x...)   -- 26 monitored ids
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3;


-- ============================================================================
-- Q5, publication snapshot panel, from the uploaded dataset.
-- ============================================================================
-- Source artifact: dune/upload_eval_2026_07_16.csv, generated by
-- dune/make_upload_csv.py from docs/evaluation_results.csv, whose hash is
-- pinned in docs/evaluation_manifest.json. Uploaded as the Dune dataset
-- morpho_stress_eval_2026_07_16.
--
-- CONFIRM the exact table reference with the editor's autocomplete after
-- upload (type "dune.bandulf." and pick the dataset); the documented pattern
-- is dune.<username>.<dataset_name>, but verify rather than assume.
--
-- Panel title: "Publication snapshot, 16 July 2026, block 25545086".
-- Ascending sort on the survival frontier puts red markets on top, which is
-- the useful reading order.
-- ============================================================================

SELECT
    market,
    tier,
    alpha_star             AS survival_frontier,
    utilization,
    insolvency_extreme_pct AS latent_insolvency_pct,
    extreme_illiq_fail     AS fails_liquidity_leg
FROM dune.bandulf.morpho_stress_eval_2026_07_16
ORDER BY alpha_star ASC;


-- ============================================================================
-- REPRODUCTION BOUNDARY
-- ============================================================================
-- Any live panel that claims to match the published snapshot must carry:
--
--     AND evt_block_time < TIMESTAMP '2026-07-17 00:00:00'
--
-- or, for an exact match, filter on evt_block_number <= 25545086.
--
-- Every panel states its regime in its title: "(live)" or "(publication
-- snapshot, 16 July 2026)". A panel that states neither is the defect this
-- file exists to prevent.
-- ============================================================================
