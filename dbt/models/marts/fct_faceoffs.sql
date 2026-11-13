-- One row per faceoff from the play-by-play, regular season and playoffs, from 2009-10 (none earlier), linked to
-- fct_games. The winning team is the event's owner team; the zone is from the winning team's point of view.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with faceoffs as (

    select * from {{ ref('stg_nhl_web__pbp_plays') }}
    where event_type = 'faceoff'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    faceoffs.event_key as faceoff_key,
    faceoffs.game_id,
    faceoffs.season,
    faceoffs.game_type,
    games.game_date,
    faceoffs.event_id,
    faceoffs.period_number,
    faceoffs.period_type,
    faceoffs.time_in_period_seconds,
    faceoffs.situation_code,
    faceoffs.event_owner_team_id as winning_team_id,
    case when faceoffs.event_owner_team_id = games.home_team_id then games.away_team_id else games.home_team_id end
        as losing_team_id,
    faceoffs.winning_player_id,
    faceoffs.losing_player_id,
    faceoffs.x_coord,
    faceoffs.y_coord,
    faceoffs.zone_code,
    faceoffs.loaded_at
from faceoffs
left join {{ ref('fct_games') }} as games on games.game_id = faceoffs.game_id
