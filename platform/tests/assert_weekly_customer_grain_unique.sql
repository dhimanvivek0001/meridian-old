-- Grain test: a customer can appear only once per week. Returns rows = FAIL.
select customer_id, week_start, count(*) as n
from {{ ref('fct_weekly_customer') }}
group by 1, 2
having count(*) > 1
