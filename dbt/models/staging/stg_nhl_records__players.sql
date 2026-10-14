-- One row per player from the NHL records site.
-- The response also carries contract and waiver fields; only biographical columns are kept here.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__player') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

players as (

    select unnest(json_extract(payload, '$.data[*]')) as player
    from latest_response

)

select
    (player ->> 'id')::bigint as player_id,
    player ->> 'fullName' as full_name,
    player ->> 'firstName' as first_name,
    player ->> 'lastName' as last_name,
    (player ->> 'birthDate')::date as birth_date,
    player ->> 'birthCity' as birth_city,
    player ->> 'birthStateProvince' as birth_state_province,
    player ->> 'birthCountry' as birth_country,
    player ->> 'nationality' as nationality,
    player ->> 'position' as position,
    player ->> 'shootsCatches' as shoots_catches,
    (player ->> 'height')::integer as height_inches,
    (player ->> 'weight')::integer as weight_pounds,
    (player ->> 'deceased')::boolean as is_deceased,
    (player ->> 'dateOfDeath')::date as death_date,
    (player ->> 'hofInductionYear')::integer as hall_of_fame_year,
    (player ->> 'isDeleted')::boolean as is_deleted
from players
