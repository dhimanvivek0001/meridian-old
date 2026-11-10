-- One row per customer who has ever bought: behaviour features as of a snapshot date.
-- The snapshot date is a variable, so we can rebuild "as of" any past date later
-- (that's how churn and CLV models get training data without peeking at the future).
{% set as_of = var('as_of_date', '2020-09-22') %}

with sales as (
    select s.*, a.product_group
    from {{ ref('fct_sales') }} s
    join {{ ref('dim_article') }} a using (article_id)
    where s.sale_date <= date '{{ as_of }}'
),
per_customer as (
    select
        customer_id,
        date '{{ as_of }}' - max(sale_date)                          as recency_days,
        date '{{ as_of }}' - min(sale_date)                          as tenure_days,
        count(distinct sale_date)                                    as frequency,
        count(*)::bigint                                             as units,
        sum(price_index)                                             as monetary,
        avg(case when sales_channel = 'online' then 1.0 else 0.0 end) as online_share,
        count(distinct product_group)                                as product_groups_bought,
        count(distinct case when sale_date > date '{{ as_of }}' - interval 91 day
                            then week_start end)                     as active_weeks_last_13
    from sales
    group by customer_id
)
select
    p.customer_id,
    p.recency_days,
    p.tenure_days,
    p.frequency,
    p.units,
    p.monetary,
    p.monetary / p.frequency                   as avg_order_value,
    p.units::double / p.frequency              as avg_items_per_order,
    p.monetary / p.units                       as avg_price_per_item,
    p.online_share,
    p.product_groups_bought,
    p.active_weeks_last_13,
    c.age,
    c.age_band,
    c.club_member_status,
    c.fashion_news_frequency
from per_customer p
join {{ ref('dim_customer') }} c using (customer_id)
