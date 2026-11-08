-- One row per calendar day. Starts on the MONDAY of the first sale's week,
-- so every week_start in the facts has a matching row here.
with days as (
    select unnest(generate_series(
        (select date_trunc('week', min(sale_date)) from {{ ref('stg_transactions') }}),
        (select max(sale_date) from {{ ref('stg_transactions') }}),
        interval 1 day
    ))::date as date_day
)
select
    date_day,
    date_trunc('week', date_day)::date   as week_start,     -- Monday
    date_trunc('month', date_day)::date  as month_start,
    year(date_day)                       as year,
    month(date_day)                      as month,
    isodow(date_day)                     as day_of_week,    -- 1 = Mon, 7 = Sun
    isodow(date_day) in (6, 7)           as is_weekend,
    case
        when month(date_day) in (12, 1, 2) then 'winter'
        when month(date_day) in (3, 4, 5)  then 'spring'
        when month(date_day) in (6, 7, 8)  then 'summer'
        else 'autumn'
    end                                  as season
from days
