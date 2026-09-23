select
    lower(market_id)                                            as market_id,
    lower(loan_asset)                                           as loan_asset_address,
    loan_asset_symbol,
    cast(loan_asset_decimals as {{ dbt.type_int() }})           as loan_asset_decimals,
    lower(collateral_asset)                                     as collateral_asset_address,
    collateral_asset_symbol,
    cast(collateral_asset_decimals as {{ dbt.type_int() }})     as collateral_asset_decimals,
    lower(oracle)                                               as oracle_address,
    oracle_type,
    lower(irm)                                                  as irm_address,
    lltv,
    cast(created_at_block as {{ dbt.type_bigint() }})           as created_at_block,
    created_at_ts,
    -- Label convention of the publication table: collateral/loan (cbBTC/USDC).
    collateral_asset_symbol || '/' || loan_asset_symbol         as market_label
from {{ source('morpho_cache', 'markets') }}
