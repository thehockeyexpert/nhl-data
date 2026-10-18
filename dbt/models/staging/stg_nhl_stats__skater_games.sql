-- One row per skater per game, regular season and playoffs, from the NHL stats API's skater summary (isGame=true).
-- Incremental: each build reads only raw responses loaded since the last build, so the nightly build does not
-- re-read the whole history (about 1.3 GB of JSON). A row seen again (overlapping windows, a corrected response)
-- replaces the earlier one for the same game and player.

{{ config(materialized='incremental', unique_key='skater_game_key', incremental_strategy='delete+insert') }}

with new_responses as (

    select *
    from {{ source('raw', 'nhl_stats__skater_game') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

),

rows as (

    select
        season,
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as skater_game
    from new_responses

),

renamed as (

    select
        (skater_game ->> 'gameId')::bigint as game_id,
        (skater_game ->> 'playerId')::bigint as player_id,
        season,
        -- The game type is the 5th and 6th digit of the game ID (2025020001 is type 02).
        ((skater_game ->> 'gameId')::bigint // 10000 % 100)::integer as game_type,
        (skater_game ->> 'gameDate')::date as game_date,
        skater_game ->> 'skaterFullName' as skater_name,
        skater_game ->> 'positionCode' as position_code,
        skater_game ->> 'teamAbbrev' as team_abbrev,
        skater_game ->> 'opponentTeamAbbrev' as opponent_abbrev,
        skater_game ->> 'homeRoad' as home_road,
        (skater_game ->> 'gamesPlayed')::integer as games_played,
        (skater_game ->> 'goals')::integer as goals,
        (skater_game ->> 'assists')::integer as assists,
        (skater_game ->> 'points')::integer as points,
        (skater_game ->> 'plusMinus')::integer as plus_minus,
        (skater_game ->> 'penaltyMinutes')::integer as penalty_minutes,
        (skater_game ->> 'evGoals')::integer as even_strength_goals,
        (skater_game ->> 'evPoints')::integer as even_strength_points,
        (skater_game ->> 'ppGoals')::integer as power_play_goals,
        (skater_game ->> 'ppPoints')::integer as power_play_points,
        (skater_game ->> 'shGoals')::integer as short_handed_goals,
        (skater_game ->> 'shPoints')::integer as short_handed_points,
        (skater_game ->> 'gameWinningGoals')::integer as game_winning_goals,
        (skater_game ->> 'otGoals')::integer as overtime_goals,
        (skater_game ->> 'shots')::integer as shots,
        (skater_game ->> 'timeOnIcePerGame')::double as time_on_ice_seconds,
        (skater_game ->> 'faceoffWinPct')::double as faceoff_win_pct,
        loaded_at
    from rows

)

select
    game_id || '-' || player_id as skater_game_key,
    *
from renamed
qualify row_number() over (partition by game_id, player_id order by loaded_at desc) = 1
