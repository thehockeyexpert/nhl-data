-- One row per team and regular season with the NHL's official totals, from the NHL stats API.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_stats__team_season') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

team_seasons as (

    select unnest(json_extract(payload, '$.data[*]')) as team_season
    from latest_response

)

select
    (team_season ->> 'seasonId')::integer || '-' || (team_season ->> 'teamId')::integer as team_season_key,
    (team_season ->> 'seasonId')::integer as season,
    (team_season ->> 'teamId')::integer as team_id,
    team_season ->> 'teamFullName' as team_name,
    (team_season ->> 'gamesPlayed')::integer as games_played,
    (team_season ->> 'wins')::integer as wins,
    (team_season ->> 'losses')::integer as losses,
    (team_season ->> 'ties')::integer as ties,
    (team_season ->> 'otLosses')::integer as ot_losses,
    (team_season ->> 'points')::integer as points,
    (team_season ->> 'goalsFor')::integer as goals_for,
    (team_season ->> 'goalsAgainst')::integer as goals_against,
    (team_season ->> 'shotsForPerGame')::double as shots_for_per_game,
    (team_season ->> 'shotsAgainstPerGame')::double as shots_against_per_game,
    (team_season ->> 'teamShutouts')::integer as team_shutouts
from team_seasons
