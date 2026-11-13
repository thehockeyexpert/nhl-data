-- One row per takeaway from the play-by-play, regular season and playoffs, from 2009-10 (none earlier), linked to
-- fct_games. player_id took the puck away; the team is the event's owner team. Counted by arena scorers, so counts
-- differ between arenas.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with takeaways as (

    select * from {{ ref('stg_nhl_web__pbp_plays') }}
    where event_type = 'takeaway'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    takeaways.event_key as takeaway_key,
    takeaways.game_id,
    takeaways.season,
    takeaways.game_type,
    games.game_date,
    takeaways.event_id,
    takeaways.period_number,
    takeaways.period_type,
    takeaways.time_in_period_seconds,
    takeaways.situation_code,
    takeaways.event_owner_team_id as team_id,
    takeaways.player_id,
    takeaways.x_coord,
    takeaways.y_coord,
    takeaways.zone_code,
    takeaways.loaded_at
from takeaways
left join {{ ref('fct_games') }} as games on games.game_id = takeaways.game_id
