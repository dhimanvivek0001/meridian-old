-- Reconciliation: weekly rollup must add back up to the line-level fact.
with f as (select count(*) as units, round(sum(price_index), 4) as rev from {{ ref('fct_sales') }}),
     w as (select sum(units) as units, round(sum(spend_index), 4) as rev from {{ ref('fct_weekly_customer') }})
select * from f, w where f.units <> w.units or f.rev <> w.rev
