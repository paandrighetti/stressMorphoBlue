{#- One long table of the four flow events with a sign convention:
    supply +, withdraw - on the supply ledger; borrow +, repay - on the
    borrow ledger. Amounts are gross flows in loan-asset units. They are
    never cumulated into a balance: interest accrues through separate
    AccrueInterest events, so sum(supply) - sum(withdraw) understates the
    outstanding position and the error grows with time and utilisation.
    Balances live in stg_morpho__market_state (contract state reads). -#}
{% set flows = [
    ('stg_morpho__events_supply',   'supply',   'supply',  1),
    ('stg_morpho__events_withdraw', 'withdraw', 'supply', -1),
    ('stg_morpho__events_borrow',   'borrow',   'borrow',  1),
    ('stg_morpho__events_repay',    'repay',    'borrow', -1),
] %}

{% for model, flow_type, ledger, sign in flows %}
select
    e.event_key,
    e.market_id,
    e.block_number,
    e.block_ts,
    e.tx_hash,
    e.log_index,
    '{{ flow_type }}'                       as flow_type,
    '{{ ledger }}'                          as ledger,
    {{ sign }}                              as flow_sign,
    e.assets                                as amount_loan_units,
    {{ sign }} * e.assets                   as signed_amount_loan_units,
    e.shares                                as shares,
    e.on_behalf                             as account,
    m.loan_asset_symbol,
    m.collateral_asset_symbol,
    m.market_label
from {{ ref(model) }} as e
inner join {{ ref('stg_morpho__markets') }} as m
    on m.market_id = e.market_id
where 1 = 1
    {{ roster_filter('e.market_id') }}
{% if not loop.last %}
union all
{% endif %}
{% endfor %}
