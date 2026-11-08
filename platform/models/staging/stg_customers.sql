select
    customer_id,
    coalesce("FN", 0) = 1                    as subscribed_fashion_news,
    coalesce("Active", 0) = 1                as is_active_communication,
    coalesce(club_member_status, 'UNKNOWN')  as club_member_status,
    -- raw data has both 'NONE' and 'None': same meaning, different spelling
    case upper(coalesce(fashion_news_frequency, 'NONE'))
        when 'REGULARLY' then 'REGULARLY'
        when 'MONTHLY'   then 'MONTHLY'
        else 'NONE'
    end                                      as fashion_news_frequency,
    cast(age as integer)                     as age,  -- null kept: missing is information
    postal_code
from {{ source('hm', 'customers') }}
