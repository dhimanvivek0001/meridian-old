-- Grain: one row per item sold. Keys point to dim_customer, dim_article, dim_date.
select
    sale_line_id,
    sale_date,
    date_trunc('week', sale_date)::date  as week_start,
    customer_id,
    article_id,
    sales_channel,
    price_index
from {{ ref('stg_transactions') }}
