-- One row per article: catalogue attributes + lifetime sales stats
with stats as (
    select
        article_id,
        min(sale_date)               as first_sale_date,
        max(sale_date)               as last_sale_date,
        count(*)                     as units_sold,
        sum(price_index)             as revenue_index,
        count(distinct customer_id)  as unique_buyers
    from {{ ref('fct_sales') }}
    group by article_id
)
select
    a.*,
    s.article_id is null             as is_never_sold,   -- cold-start items for M8/M9
    s.first_sale_date,
    s.last_sale_date,
    coalesce(s.units_sold, 0)        as units_sold,
    coalesce(s.revenue_index, 0)     as revenue_index,
    coalesce(s.unique_buyers, 0)     as unique_buyers
from {{ ref('stg_articles') }} a
left join stats s using (article_id)
