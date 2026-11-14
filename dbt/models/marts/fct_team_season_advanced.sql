-- One row per team per regular season from 1955-56 (the first season goalies' shots against are recorded):
-- shot-attempt shares (CF%, FF%), shooting %, save % and PDO, in all situations and at 5-on-5.
-- - All situations, shooting % and save %: from fct_goalie_games, so they count goals and shots against goalies.
--   Empty-net goals and shootouts are left out (they are not charged to a goalie), so a team's shooting % is the
--   mirror of its opponents' save %. From 1955-56.
-- - CF%, FF% and every 5-on-5 column: from fct_team_game_shot_attempts, 2009-10 onward; empty before.
--   5-on-5 means both goalies in, so it has no empty-net goals.
-- - PDO = (shooting % + save %) x 100, so 100 is league average.
-- Shares and percentages are fractions from 0 to 1 (0.523 is 52.3%).

{{ config(materialized='table', tags=['advanced']) }}

with goalie_games as (

    select * from {{ ref('fct_goalie_games') }}
    where game_type = 2 and season >= 19551956

),

-- Goals and shots against each team's goalies (save %), and against its opponents' goalies (shooting %).
against_goalies as (

    select season, team_id, sum(goals_against) as goals_against, sum(shots_against) as shots_against
    from goalie_games
    group by season, team_id

),

on_opponent_goalies as (

    select season, opponent_team_id as team_id, sum(goals_against) as goals_for, sum(shots_against) as shots_for
    from goalie_games
    group by season, opponent_team_id

),

team_seasons as (

    select season, team_id, count(*) as games_played
    from {{ ref('fct_team_games') }}
    where game_type = 2 and season >= 19551956
    group by season, team_id

),

attempts as (

    select
        season,
        team_id,
        {% for column in ['corsi', 'fenwick', 'shots_on_goal', 'goals'] -%}
        sum({{ column }}_for) as {{ column }}_for,
        sum({{ column }}_against) as {{ column }}_against,
        sum({{ column }}_for_5v5) as {{ column }}_for_5v5,
        sum({{ column }}_against_5v5) as {{ column }}_against_5v5{{ ',' if not loop.last }}
        {% endfor %}
    from {{ ref('fct_team_game_shot_attempts') }}
    where game_type = 2
    group by season, team_id

),

shares as (

    select
        team_seasons.season,
        team_seasons.team_id,
        team_seasons.games_played,
        on_opponent_goalies.goals_for as goalie_goals_for,
        on_opponent_goalies.shots_for as goalie_shots_for,
        against_goalies.goals_against as goalie_goals_against,
        against_goalies.shots_against as goalie_shots_against,
        attempts.corsi_for,
        attempts.corsi_against,
        attempts.fenwick_for,
        attempts.fenwick_against,
        attempts.corsi_for_5v5,
        attempts.corsi_against_5v5,
        attempts.fenwick_for_5v5,
        attempts.fenwick_against_5v5,
        attempts.goals_for_5v5,
        attempts.goals_against_5v5,
        attempts.shots_on_goal_for_5v5,
        attempts.shots_on_goal_against_5v5,

        attempts.corsi_for / nullif(attempts.corsi_for + attempts.corsi_against, 0) as cf_pct,
        attempts.fenwick_for / nullif(attempts.fenwick_for + attempts.fenwick_against, 0) as ff_pct,
        on_opponent_goalies.goals_for / nullif(on_opponent_goalies.shots_for, 0) as shooting_pct,
        1 - against_goalies.goals_against / nullif(against_goalies.shots_against, 0) as save_pct,

        attempts.corsi_for_5v5 / nullif(attempts.corsi_for_5v5 + attempts.corsi_against_5v5, 0) as cf_pct_5v5,
        attempts.fenwick_for_5v5 / nullif(attempts.fenwick_for_5v5 + attempts.fenwick_against_5v5, 0) as ff_pct_5v5,
        attempts.goals_for_5v5 / nullif(attempts.shots_on_goal_for_5v5, 0) as shooting_pct_5v5,
        1 - attempts.goals_against_5v5 / nullif(attempts.shots_on_goal_against_5v5, 0) as save_pct_5v5
    from team_seasons
    left join on_opponent_goalies
        on on_opponent_goalies.season = team_seasons.season and on_opponent_goalies.team_id = team_seasons.team_id
    left join against_goalies
        on against_goalies.season = team_seasons.season and against_goalies.team_id = team_seasons.team_id
    left join attempts
        on attempts.season = team_seasons.season and attempts.team_id = team_seasons.team_id

)

select
    season || '-' || team_id as team_season_key,
    *,
    (shooting_pct + save_pct) * 100 as pdo,
    (shooting_pct_5v5 + save_pct_5v5) * 100 as pdo_5v5
from shares
