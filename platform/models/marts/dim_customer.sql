-- One row per customer: profile + lifetime purchase stats
with stats as (
    select
        customer_id,
        min(sale_date)                                  as first_purchase_date,
        max(sale_date)                                  as last_purchase_date,
        count(distinct sale_date)                       as purchase_days,  -- proxy for orders
        count(*)                                        as units_bought,
        sum(price_index)                                as spend_index,
        avg(case when sales_channel = 'online' then 1.0 else 0.0 end) as online_share
    from {{ ref('fct_sales') }}
    group by customer_id
)
select
    c.*,
    case
        when c.age is null then 'unknown'
        when c.age < 25 then '16-24'
        when c.age < 35 then '25-34'
        when c.age < 45 then '35-44'
        when c.age < 55 then '45-54'
        else '55+'
    end                                       as age_band,
    s.customer_id is not null                 as has_purchased,
    s.first_purchase_date,
    s.last_purchase_date,
    coalesce(s.purchase_days, 0)              as purchase_days,
    coalesce(s.units_bought, 0)               as units_bought,
    coalesce(s.spend_index, 0)                as spend_index,
    s.online_share
from {{ ref('stg_customers') }} c
left join stats s using (customer_id)
