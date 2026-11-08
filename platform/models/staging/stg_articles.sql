select
    article_id,
    product_code,
    prod_name                    as product_name,
    product_type_name            as product_type,
    product_group_name           as product_group,
    graphical_appearance_name    as pattern,
    colour_group_name            as colour,
    perceived_colour_value_name  as colour_tone,
    perceived_colour_master_name as colour_family,
    department_name              as department,
    index_name                   as index_name,
    index_group_name             as index_group,
    section_name                 as section,
    garment_group_name           as garment_group,
    detail_desc                  as description
from {{ source('hm', 'articles') }}
