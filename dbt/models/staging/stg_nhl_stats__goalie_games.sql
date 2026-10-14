-- One row per goalie per game, regular season and playoffs, from the NHL stats API.

with latest_responses as (

    select *
    from {{ source('raw', 'nhl_stats__goalie_game') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

rows as (

    select
        season,
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as goalie_game
    from latest_responses

),

renamed as (

    select
        (goalie_game ->> 'gameId')::bigint as game_id,
        season,
        -- The game type is the 5th and 6th digit of the game ID (2025020001 is type 02).
        ((goalie_game ->> 'gameId')::bigint // 10000 % 100)::integer as game_type,
        (goalie_game ->> 'gameDate')::date as game_date,
        (goalie_game ->> 'playerId')::bigint as player_id,
        goalie_game ->> 'goalieFullName' as goalie_name,
        goalie_game ->> 'teamAbbrev' as team_abbrev,
        goalie_game ->> 'opponentTeamAbbrev' as opponent_abbrev,
        goalie_game ->> 'homeRoad' as home_road,
        (goalie_game ->> 'gamesStarted')::integer as games_started,
        (goalie_game ->> 'wins')::integer as wins,
        (goalie_game ->> 'losses')::integer as losses,
        (goalie_game ->> 'ties')::integer as ties,
        (goalie_game ->> 'otLosses')::integer as ot_losses,
        (goalie_game ->> 'shutouts')::integer as shutouts,
        (goalie_game ->> 'goalsAgainst')::integer as goals_against,
        (goalie_game ->> 'shotsAgainst')::integer as shots_against,
        (goalie_game ->> 'saves')::integer as saves,
        (goalie_game ->> 'timeOnIce')::integer as time_on_ice_seconds,
        (goalie_game ->> 'goals')::integer as goals,
        (goalie_game ->> 'assists')::integer as assists,
        (goalie_game ->> 'penaltyMinutes')::integer as penalty_minutes,
        loaded_at
    from rows

)

select
    game_id || '-' || player_id as goalie_game_key,
    *
from renamed
qualify row_number() over (partition by game_id, player_id order by loaded_at desc) = 1
