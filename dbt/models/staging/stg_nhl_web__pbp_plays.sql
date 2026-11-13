-- One row per faceoff, giveaway, takeaway, stoppage, or period start or end from the play-by-play, regular season and
-- playoffs; the NHL records these from 2009-10 (decided 2026-11-13). raw.nhl_web__pbp_play holds only these events; the
-- full responses stay as compressed files on the owner's laptop.
-- Incremental, like stg_nhl_web__pbp_events: a game loaded again replaces all of that game's earlier rows.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with new_rows as (

    select *
    from {{ source('raw', 'nhl_web__pbp_play') }}
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
        try_cast(split_part(event ->> 'timeInPeriod', ':', 1) as integer) * 60
            + try_cast(split_part(event ->> 'timeInPeriod', ':', 2) as integer) as time_in_period_seconds,
        event ->> 'situationCode' as situation_code,
        event ->> 'homeTeamDefendingSide' as home_team_defending_side,
        (event -> 'details' ->> 'eventOwnerTeamId')::integer as event_owner_team_id,
        -- faceoffs
        (event -> 'details' ->> 'winningPlayerId')::bigint as winning_player_id,
        (event -> 'details' ->> 'losingPlayerId')::bigint as losing_player_id,
        -- giveaways and takeaways
        (event -> 'details' ->> 'playerId')::bigint as player_id,
        -- stoppages
        event -> 'details' ->> 'reason' as stoppage_reason,
        event -> 'details' ->> 'secondaryReason' as stoppage_secondary_reason,
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
