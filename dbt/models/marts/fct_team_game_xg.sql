-- One row per team per finished regular-season or playoff game from 2010-11: expected goals for and against (our
-- model, docs/definitions.md D33) and xGF% = xGF / (xGF + xGA), in all situations and at 5-on-5 (both goalies in),
-- with the actual non-shootout goals beside them. From fct_shot_xg.

{{ config(materialized='table', tags=['advanced', 'xg']) }}

with team_games as (

    select * from {{ ref('fct_team_games') }}
    where season >= 20102011 and game_type in (2, 3)

),

shots as (

    select game_id, shooting_team_id, defending_team_id, xg, is_goal, is_5v5
    from {{ ref('fct_shot_xg') }}

),

by_team as (

    select game_id, shooting_team_id as team_id, true as is_for, xg, is_goal, is_5v5 from shots
    union all
    select game_id, defending_team_id as team_id, false as is_for, xg, is_goal, is_5v5 from shots

),

totals as (

    select
        game_id,
        team_id,
        sum(xg) filter (where is_for) as xgf,
        sum(xg) filter (where not is_for) as xga,
        count(*) filter (where is_for and is_goal) as goals_for,
        count(*) filter (where not is_for and is_goal) as goals_against,
        sum(xg) filter (where is_for and is_5v5) as xgf_5v5,
        sum(xg) filter (where not is_for and is_5v5) as xga_5v5,
        count(*) filter (where is_for and is_5v5 and is_goal) as goals_for_5v5,
        count(*) filter (where not is_for and is_5v5 and is_goal) as goals_against_5v5
    from by_team
    group by game_id, team_id

),

filled as (

    select
        team_games.team_game_key,
        team_games.game_id,
        team_games.season,
        team_games.game_type,
        team_games.game_date,
        team_games.team_id,
        team_games.opponent_team_id,
        team_games.is_home,
        coalesce(totals.xgf, 0) as xgf,
        coalesce(totals.xga, 0) as xga,
        coalesce(totals.goals_for, 0) as goals_for,
        coalesce(totals.goals_against, 0) as goals_against,
        coalesce(totals.xgf_5v5, 0) as xgf_5v5,
        coalesce(totals.xga_5v5, 0) as xga_5v5,
        coalesce(totals.goals_for_5v5, 0) as goals_for_5v5,
        coalesce(totals.goals_against_5v5, 0) as goals_against_5v5
    from team_games
    left join totals on totals.game_id = team_games.game_id and totals.team_id = team_games.team_id

)

select
    *,
    xgf / nullif(xgf + xga, 0) as xgf_pct,
    xgf_5v5 / nullif(xgf_5v5 + xga_5v5, 0) as xgf_pct_5v5
from filled
