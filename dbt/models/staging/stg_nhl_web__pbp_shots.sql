-- One row per shot event (shot on goal, missed shot, blocked shot, goal) from the play-by-play, regular season and
-- playoffs, from 2007-08. raw.nhl_web__pbp_shot holds only these events; the full responses stay as compressed files
-- on the owner's laptop (docs/decisions.md, 2026-11-10).
-- Incremental: each build reads only raw rows loaded since the last build. A game loaded again (a corrected response)
-- replaces all of that game's earlier rows, so events dropped by the correction disappear too.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with new_rows as (

    select *
    from {{ source('raw', 'nhl_web__pbp_shot') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
    -- Only the newest version of each game.
    qualify loaded_at = max(loaded_at) over (partition by game_id)

),

renamed as (

    select
        game_id,
        season,
        -- The game type is the 5th and 6th digit of the game ID (2025020001 is type 02).
        (game_id // 10000 % 100)::integer as game_type,
        (event ->> 'eventId')::integer as event_id,
        (event ->> 'sortOrder')::integer as sort_order,
        event ->> 'typeDescKey' as event_type,
        (event -> 'periodDescriptor' ->> 'number')::integer as period_number,
        event -> 'periodDescriptor' ->> 'periodType' as period_type,
        split_part(event ->> 'timeInPeriod', ':', 1)::integer * 60
            + split_part(event ->> 'timeInPeriod', ':', 2)::integer as time_in_period_seconds,
        event ->> 'situationCode' as situation_code,
        event ->> 'homeTeamDefendingSide' as home_team_defending_side,
        (event -> 'details' ->> 'eventOwnerTeamId')::integer as event_owner_team_id,
        -- A goal names its shooter scoringPlayerId; the other shot events name it shootingPlayerId.
        coalesce(event -> 'details' ->> 'shootingPlayerId', event -> 'details' ->> 'scoringPlayerId')::bigint
            as shooting_player_id,
        (event -> 'details' ->> 'goalieInNetId')::bigint as goalie_in_net_id,
        (event -> 'details' ->> 'blockingPlayerId')::bigint as blocking_player_id,
        (event -> 'details' ->> 'assist1PlayerId')::bigint as assist1_player_id,
        (event -> 'details' ->> 'assist2PlayerId')::bigint as assist2_player_id,
        event -> 'details' ->> 'shotType' as shot_type,
        (event -> 'details' ->> 'xCoord')::integer as x_coord,
        (event -> 'details' ->> 'yCoord')::integer as y_coord,
        event -> 'details' ->> 'zoneCode' as zone_code,
        event -> 'details' ->> 'reason' as reason,
        loaded_at
    from new_rows

)

select
    game_id || '-' || event_id as shot_key,
    *
from renamed
