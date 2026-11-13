-- One row per stoppage of play from the play-by-play, regular season and playoffs, from 2009-10 (none earlier), linked
-- to fct_games, with the NHL's reason (icing, offside, puck in netting...) and any secondary reason (a TV timeout...).

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with stoppages as (

    select * from {{ ref('stg_nhl_web__pbp_plays') }}
    where event_type = 'stoppage'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    stoppages.event_key as stoppage_key,
    stoppages.game_id,
    stoppages.season,
    stoppages.game_type,
    games.game_date,
    stoppages.event_id,
    stoppages.period_number,
    stoppages.period_type,
    stoppages.time_in_period_seconds,
    stoppages.situation_code,
    stoppages.stoppage_reason,
    stoppages.stoppage_secondary_reason,
    stoppages.loaded_at
from stoppages
left join {{ ref('fct_games') }} as games on games.game_id = stoppages.game_id
