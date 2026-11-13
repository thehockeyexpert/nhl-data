-- One row per giveaway from the play-by-play, regular season and playoffs, from 2009-10 (none earlier), linked to
-- fct_games. player_id gave the puck away; the team is the event's owner team. Counted by arena scorers, so counts
-- differ between arenas.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with giveaways as (

    select * from {{ ref('stg_nhl_web__pbp_plays') }}
    where event_type = 'giveaway'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    giveaways.event_key as giveaway_key,
    giveaways.game_id,
    giveaways.season,
    giveaways.game_type,
    games.game_date,
    giveaways.event_id,
    giveaways.period_number,
    giveaways.period_type,
    giveaways.time_in_period_seconds,
    giveaways.situation_code,
    giveaways.event_owner_team_id as team_id,
    giveaways.player_id,
    giveaways.x_coord,
    giveaways.y_coord,
    giveaways.zone_code,
    giveaways.loaded_at
from giveaways
left join {{ ref('fct_games') }} as games on games.game_id = giveaways.game_id
