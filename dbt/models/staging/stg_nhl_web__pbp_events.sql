-- One row per hit or penalty from the play-by-play, regular season and playoffs, 1917-18 to today (hits
-- from 2009-10) (decided 2026-11-11).
-- raw.nhl_web__pbp_event holds only these events; the full responses stay as compressed files on the owner's laptop.
-- Incremental, like stg_nhl_web__pbp_shots: a game loaded again replaces all of that game's earlier rows.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with new_rows as (

    select *
    from {{ source('raw', 'nhl_web__pbp_event') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
    qualify loaded_at = max(loaded_at) over (partition by game_id)

),

renamed as (

    select
        game_id,
        season,
        (game_id // 10000 % 100)::integer as game_type,
        (event ->> 'eventId')::integer as event_id,
        (event ->> 'sortOrder')::integer as sort_order,
        event ->> 'typeDescKey' as event_type,
        (event -> 'periodDescriptor' ->> 'number')::integer as period_number,
        event -> 'periodDescriptor' ->> 'periodType' as period_type,
        -- try_cast: a malformed clock (two in 1985-86, e.g. '0M:48') becomes null rather than failing the build
        try_cast(split_part(event ->> 'timeInPeriod', ':', 1) as integer) * 60
            + try_cast(split_part(event ->> 'timeInPeriod', ':', 2) as integer) as time_in_period_seconds,
        event ->> 'situationCode' as situation_code,
        (event -> 'details' ->> 'eventOwnerTeamId')::integer as event_owner_team_id,
        -- hits
        (event -> 'details' ->> 'hittingPlayerId')::bigint as hitting_player_id,
        (event -> 'details' ->> 'hitteePlayerId')::bigint as hittee_player_id,
        -- penalties
        event -> 'details' ->> 'typeCode' as penalty_type_code,
        event -> 'details' ->> 'descKey' as penalty_desc_key,
        (event -> 'details' ->> 'duration')::integer as penalty_minutes,
        (event -> 'details' ->> 'committedByPlayerId')::bigint as committed_by_player_id,
        (event -> 'details' ->> 'drawnByPlayerId')::bigint as drawn_by_player_id,
        (event -> 'details' ->> 'servedByPlayerId')::bigint as served_by_player_id,
        (event -> 'details' ->> 'xCoord')::integer as x_coord,
        (event -> 'details' ->> 'yCoord')::integer as y_coord,
        event -> 'details' ->> 'zoneCode' as zone_code,
        loaded_at
    from new_rows

)

select
    game_id || '-' || event_id as event_key,
    *
from renamed
