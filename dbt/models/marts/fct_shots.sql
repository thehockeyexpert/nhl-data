-- One row per shot attempt (shot on goal, missed shot, blocked shot, goal) from the play-by-play, regular season and
-- playoffs, from 2007-08, linked to fct_games. Shootout attempts are kept and flagged (is_shootout).
-- The shooting team is the event's owner team: in 2025-26 that is the shooter's team for every shot type, blocked shots
-- included (all 163,818 events checked against each game's roster, 2026-11-10). Other seasons are to be checked before
-- they are loaded.
-- Incremental: each build replaces only the games new in staging.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with shots as (

    select * from {{ ref('stg_nhl_web__pbp_shots') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

),

games as (

    select * from {{ ref('fct_games') }}

)

select
    shots.shot_key,
    shots.game_id,
    shots.season,
    shots.game_type,
    games.game_type_label,
    games.game_date,
    shots.event_id,
    shots.sort_order,
    shots.event_type,
    shots.event_type = 'goal' as is_goal,
    shots.event_type in ('goal', 'shot-on-goal') as is_on_goal,
    shots.period_type = 'SO' as is_shootout,
    shots.period_number,
    shots.period_type,
    shots.time_in_period_seconds,
    shots.situation_code,
    shots.event_owner_team_id as shooting_team_id,
    shots.event_owner_team_id = games.home_team_id as is_home_shooter,
    case when shots.event_owner_team_id = games.home_team_id then games.away_team_id else games.home_team_id end
        as defending_team_id,
    shots.shooting_player_id,
    shots.goalie_in_net_id,
    shots.blocking_player_id,
    shots.assist1_player_id,
    shots.assist2_player_id,
    shots.shot_type,
    shots.x_coord,
    shots.y_coord,
    shots.zone_code,
    shots.home_team_defending_side,
    shots.reason,
    shots.loaded_at
from shots
left join games on games.game_id = shots.game_id
