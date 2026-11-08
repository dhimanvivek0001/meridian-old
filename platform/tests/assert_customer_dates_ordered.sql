-- Logic: nobody's last purchase can come before their first.
select customer_id
from {{ ref('dim_customer') }}
where last_purchase_date < first_purchase_date
