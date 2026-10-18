-- One row per skater per game (regular season and playoffs), linked to fct_games.
-- The stats API gives a team abbreviation but no team ID, and abbreviations are reused across eras, so the team comes
-- from the game: the home team if the skater's row is H, otherwise the away team (as in fct_goalie_games).
-- This splits a traded player's season by team. Incremental: each build adds only rows new in staging.

{{ config(materialized='incremental', unique_key='skater_game_key', incremental_strategy='delete+insert') }}

with skater_games as (

    select * from {{ ref('stg_nhl_stats__skater_games') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

),

games as (

    select * from {{ ref('fct_games') }}

)

select
    skater_games.skater_game_key,
    skater_games.game_id,
    skater_games.season,
    skater_games.game_type,
    games.game_type_label,
    skater_games.game_date,
    skater_games.player_id,
    skater_games.skater_name,
    skater_games.position_code,
    skater_games.home_road = 'H' as is_home,
    case when skater_games.home_road = 'H' then games.home_team_id else games.away_team_id end as team_id,
    case when skater_games.home_road = 'H' then games.away_team_id else games.home_team_id end as opponent_team_id,
    skater_games.team_abbrev,
    skater_games.goals,
    skater_games.assists,
    skater_games.points,
    skater_games.plus_minus,
    skater_games.penalty_minutes,
    skater_games.even_strength_goals,
    skater_games.even_strength_points,
    skater_games.power_play_goals,
    skater_games.power_play_points,
    skater_games.short_handed_goals,
    skater_games.short_handed_points,
    skater_games.game_winning_goals,
    skater_games.overtime_goals,
    skater_games.shots,
    skater_games.time_on_ice_seconds,
    skater_games.faceoff_win_pct,
    skater_games.loaded_at
from skater_games
left join games on games.game_id = skater_games.game_id
