-- One row per NHL franchise, from the NHL records site.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__franchise') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

franchises as (

    select unnest(json_extract(payload, '$.data[*]')) as franchise
    from latest_response

)

select
    (franchise ->> 'id')::integer as franchise_id,
    franchise ->> 'fullName' as franchise_name,
    (franchise ->> 'firstSeasonId')::integer as first_season,
    (franchise ->> 'lastSeasonId')::integer as last_season,
    (franchise ->> 'mostRecentTeamId')::integer as most_recent_team_id
from franchises
