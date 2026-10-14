-- One row per trophy or award from the NHL records site.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__trophy') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

trophies as (

    select unnest(json_extract(payload, '$.data[*]')) as trophy
    from latest_response

)

select
    (trophy ->> 'id')::integer as trophy_id,
    trophy ->> 'name' as trophy_name,
    trophy ->> 'shortName' as short_name,
    (trophy ->> 'categoryId')::integer as category_id
from trophies
