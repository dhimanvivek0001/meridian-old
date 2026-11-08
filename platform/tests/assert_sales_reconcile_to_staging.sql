-- Reconciliation: gold must hold exactly the same rows and revenue as staging.
with s as (select count(*) as n, round(sum(price_index), 4) as rev from {{ ref('stg_transactions') }}),
     f as (select count(*) as n, round(sum(price_index), 4) as rev from {{ ref('fct_sales') }})
select * from s, f where s.n <> f.n or s.rev <> f.rev
