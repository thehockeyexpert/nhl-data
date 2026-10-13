-- One row per team identity and game type (regular season, playoffs), from the NHL records site.
-- Used for the seasons each team identity played.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__franchise_team_totals') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

totals as (

    select unnest(json_extract(payload, '$.data[*]')) as total
    from latest_response

)

select
    (total ->> 'teamId')::integer as team_id,
    (total ->> 'franchiseId')::integer as franchise_id,
    (total ->> 'gameTypeId')::integer as game_type,
    total ->> 'teamName' as team_name,
    (total ->> 'firstSeasonId')::integer as first_season,
    -- Empty for a team that is still playing.
    (total ->> 'lastSeasonId')::integer as last_season,
    (total ->> 'activeTeam')::boolean as is_active_team,
    (total ->> 'gamesPlayed')::integer as games_played
from totals
