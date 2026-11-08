{{ config(materialized='table') }}

-- One row per item bought. No natural key: the same customer can buy the
-- same article twice on the same day, so identical rows are REAL sales.
-- We never dedupe; we add a surrogate key instead.
select
    row_number() over (order by t_dat, customer_id, article_id) as sale_line_id,
    t_dat                                    as sale_date,
    customer_id,
    article_id,
    price                                    as price_index,  -- scaled, not euros
    case sales_channel_id
        when 1 then 'store'                  -- assumption: H&M never published
        when 2 then 'online'                 -- the mapping; 2 = online is the
    end                                      as sales_channel -- community consensus
from {{ source('hm', 'transactions_train') }}
