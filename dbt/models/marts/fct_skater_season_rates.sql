-- One row per skater per regular season from 1997-98 (the first season skater time on ice is recorded): goals,
-- assists, points and shots per 60 minutes of ice time, all teams combined. Summed from fct_skater_games.
-- Rates need a minimum sample (docs/definitions.md, D05): toi_minutes and games_played are here to filter on, and
-- meets_d05_minimum applies D05's single-season rule (at least half the most games any team played that season).

{{ config(materialized='table', tags=['advanced']) }}

with skater_games as (

    select * from {{ ref('fct_skater_games') }}
    where game_type = 2 and season >= 19971998

),

team_games as (

    -- "Team games" in D05: the most games any team played that season (works for short and unfinished seasons).
    select season, max(games) as team_games
    from (
        select season, team_id, count(*) as games
        from {{ ref('fct_team_games') }}
        where game_type = 2 and season >= 19971998
        group by season, team_id
    )
    group by season

),

totals as (

    select
        player_id,
        season,
        any_value(skater_name order by game_date desc) as skater_name,
        any_value(position_code order by game_date desc) as position_code,
        count(*) as games_played,
        sum(time_on_ice_seconds) as time_on_ice_seconds,
        sum(goals) as goals,
        sum(assists) as assists,
        sum(points) as points,
        sum(shots) as shots
    from skater_games
    group by player_id, season

)

select
    totals.season || '-2-' || totals.player_id as skater_season_key,
    totals.player_id,
    totals.season,
    totals.skater_name,
    totals.position_code,
    totals.games_played,
    totals.time_on_ice_seconds,
    round(totals.time_on_ice_seconds / 60.0, 1) as toi_minutes,
    totals.goals,
    totals.assists,
    totals.points,
    totals.shots,
    totals.goals * 3600.0 / nullif(totals.time_on_ice_seconds, 0) as goals_per_60,
    totals.assists * 3600.0 / nullif(totals.time_on_ice_seconds, 0) as assists_per_60,
    totals.points * 3600.0 / nullif(totals.time_on_ice_seconds, 0) as points_per_60,
    totals.shots * 3600.0 / nullif(totals.time_on_ice_seconds, 0) as shots_per_60,
    team_games.team_games,
    totals.games_played >= team_games.team_games / 2.0 as meets_d05_minimum
from totals
inner join team_games on team_games.season = totals.season
