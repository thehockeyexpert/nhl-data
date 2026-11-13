-- One row per entry of the NHL's shift charts (stats API), regular season and playoffs, from 2010-11: shifts
-- (type_code 517) and goal markers (505). raw.nhl_stats__shift holds the entries; the full charts stay as compressed
-- files on the owner's laptop (decided 2026-11-13).
-- Incremental, like stg_nhl_web__pbp_plays: a game loaded again replaces all of that game's earlier rows.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['shifts']) }}

with new_rows as (

    select *
    from {{ source('raw', 'nhl_stats__shift') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
    qualify loaded_at = max(loaded_at) over (partition by game_id)

),

renamed as (

    select
        (event ->> 'id')::bigint as shift_id,
        game_id,
        season,
        (game_id // 10000 % 100)::integer as game_type,
        (event ->> 'typeCode')::integer as type_code,
        (event ->> 'playerId')::bigint as player_id,
        (event ->> 'teamId')::integer as team_id,
        event ->> 'teamAbbrev' as team_abbrev,
        (event ->> 'period')::integer as period_number,
        (event ->> 'shiftNumber')::integer as shift_number,
        try_cast(split_part(event ->> 'startTime', ':', 1) as integer) * 60
            + try_cast(split_part(event ->> 'startTime', ':', 2) as integer) as start_seconds,
        try_cast(split_part(event ->> 'endTime', ':', 1) as integer) * 60
            + try_cast(split_part(event ->> 'endTime', ':', 2) as integer) as end_seconds,
        try_cast(split_part(event ->> 'duration', ':', 1) as integer) * 60
            + try_cast(split_part(event ->> 'duration', ':', 2) as integer) as duration_seconds,
        (event ->> 'eventNumber')::integer as event_number,
        event ->> 'eventDescription' as event_description,
        event ->> 'detailCode' as detail_code,
        loaded_at
    from new_rows

)

select * from renamed
