-- Grain: one row per customer per week IN WHICH THEY BOUGHT (sparse).
-- A full grid (1.37M customers x 105 weeks = 144M rows) is built later only where a model needs it.
select
    customer_id,
    week_start,
    count(*)                                         as units,
    sum(price_index)                                 as spend_index,
    count(distinct sale_date)                        as purchase_days,
    count(distinct article_id)                       as distinct_articles,
    sum(case when sales_channel = 'online' then 1 else 0 end) as online_units
from {{ ref('fct_sales') }}
group by customer_id, week_start
