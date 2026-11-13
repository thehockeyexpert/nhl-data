-- One row per penalty from the play-by-play, regular season and playoffs, 1917-18 to today, linked to fct_games.
-- A fight is a fighting major (definition 1, owner 2026-11-11): one fighting penalty is one fight for that player.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with penalties as (

    select * from {{ ref('stg_nhl_web__pbp_events') }}
    where event_type = 'penalty'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    penalties.event_key as penalty_key,
    penalties.game_id,
    penalties.season,
    penalties.game_type,
    games.game_date,
    penalties.event_id,
    penalties.period_number,
    penalties.period_type,
    penalties.time_in_period_seconds,
    penalties.situation_code,
    penalties.event_owner_team_id as penalized_team_id,
    penalties.committed_by_player_id,
    penalties.drawn_by_player_id,
    penalties.served_by_player_id,
    penalties.penalty_type_code,
    penalties.penalty_desc_key,
    penalties.penalty_minutes,
    penalties.penalty_desc_key = 'fighting' as is_fight,
    penalties.x_coord,
    penalties.y_coord,
    penalties.zone_code,
    penalties.loaded_at
from penalties
left join {{ ref('fct_games') }} as games on games.game_id = penalties.game_id
