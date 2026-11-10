-- Sanity: nothing negative, recency can't exceed tenure, shares between 0 and 1.
select customer_id
from {{ ref('customer_features') }}
where recency_days < 0
   or recency_days > tenure_days
   or frequency < 1
   or online_share not between 0 and 1
   or active_weeks_last_13 > 14
