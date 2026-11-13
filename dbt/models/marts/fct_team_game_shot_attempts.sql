-- One row per team per finished regular-season or playoff game from 2009-10 (the first season the play-by-play records
-- missed and blocked shots): shot attempts (Corsi), unblocked attempts (Fenwick), shots on goal and goals, for and
-- against, in all situations and at 5-on-5. Built from fct_shots, shootouts left out.
-- - Shooting team: fct_shots.shooting_team_id is the shooter's team for every shot type, blocked shots included
--   (checked 2026-11-13: on 115,676 of 115,689 blocked shots in three seasons the shooter played for that team; the
--   other 13 have no player-game row, and none played for the blocking team).
-- - Blocked shots count as attempts for the shooting team whoever blocked them, including the NHL's
--   "teammate-blocked" shots from 2023-24 (owner's decision, 2026-11-13); teammate_blocked_for shows how many.
-- - 5-on-5: situation_code '1551' (away goalie in, 5 away skaters, 5 home skaters, home goalie in).
-- - Goals include empty-net goals; the shootout goal a shootout win adds to the final score is not a goal here.

{{ config(materialized='table', tags=['advanced']) }}

with team_games as (

    select * from {{ ref('fct_team_games') }}
    where season >= 20092010 and game_type in (2, 3)

),

shots as (

    select
        game_id,
        shooting_team_id,
        defending_team_id,
        event_type <> 'blocked-shot' as is_unblocked,
        is_on_goal,
        is_goal,
        reason = 'teammate-blocked' as is_teammate_blocked,
        situation_code = '1551' as is_5v5
    from {{ ref('fct_shots') }}
    where not is_shootout
      and season >= 20092010
      and game_type in (2, 3)
      and event_type in ('goal', 'shot-on-goal', 'missed-shot', 'blocked-shot')

),

-- Each shot counted once for the shooting team and once against the defending team.
by_team as (

    select game_id, shooting_team_id as team_id, true as is_for, * exclude (game_id, shooting_team_id, defending_team_id)
    from shots
    union all
    select game_id, defending_team_id as team_id, false as is_for, * exclude (game_id, shooting_team_id, defending_team_id)
    from shots

),

totals as (

    select
        game_id,
        team_id,
        count(*) filter (where is_for) as corsi_for,
        count(*) filter (where not is_for) as corsi_against,
        count(*) filter (where is_for and is_unblocked) as fenwick_for,
        count(*) filter (where not is_for and is_unblocked) as fenwick_against,
        count(*) filter (where is_for and is_on_goal) as shots_on_goal_for,
        count(*) filter (where not is_for and is_on_goal) as shots_on_goal_against,
        count(*) filter (where is_for and is_goal) as goals_for,
        count(*) filter (where not is_for and is_goal) as goals_against,
        count(*) filter (where is_for and is_teammate_blocked) as teammate_blocked_for,
        count(*) filter (where is_5v5 and is_for) as corsi_for_5v5,
        count(*) filter (where is_5v5 and not is_for) as corsi_against_5v5,
        count(*) filter (where is_5v5 and is_for and is_unblocked) as fenwick_for_5v5,
        count(*) filter (where is_5v5 and not is_for and is_unblocked) as fenwick_against_5v5,
        count(*) filter (where is_5v5 and is_for and is_on_goal) as shots_on_goal_for_5v5,
        count(*) filter (where is_5v5 and not is_for and is_on_goal) as shots_on_goal_against_5v5,
        count(*) filter (where is_5v5 and is_for and is_goal) as goals_for_5v5,
        count(*) filter (where is_5v5 and not is_for and is_goal) as goals_against_5v5
    from by_team
    group by game_id, team_id

)

select
    team_games.team_game_key,
    team_games.game_id,
    team_games.season,
    team_games.game_type,
    team_games.game_date,
    team_games.team_id,
    team_games.opponent_team_id,
    team_games.is_home,
    {% for column in ['corsi', 'fenwick', 'shots_on_goal', 'goals'] -%}
    coalesce(totals.{{ column }}_for, 0) as {{ column }}_for,
    coalesce(totals.{{ column }}_against, 0) as {{ column }}_against,
    {% endfor -%}
    coalesce(totals.teammate_blocked_for, 0) as teammate_blocked_for,
    {% for column in ['corsi', 'fenwick', 'shots_on_goal', 'goals'] -%}
    coalesce(totals.{{ column }}_for_5v5, 0) as {{ column }}_for_5v5,
    coalesce(totals.{{ column }}_against_5v5, 0) as {{ column }}_against_5v5{{ ',' if not loop.last }}
    {% endfor %}
from team_games
left join totals on totals.game_id = team_games.game_id and totals.team_id = team_games.team_id
