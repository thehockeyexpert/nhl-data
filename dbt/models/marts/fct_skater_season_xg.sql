-- One row per player per season and game type (regular season 2, playoffs 3) from 2010-11: unblocked shot attempts,
-- goals and expected goals (our model, docs/definitions.md D33), from fct_shot_xg. goals_above_expected = goals - xG
-- (S25). Goals here are the player's own non-shootout goals from the play-by-play, empty-net goals included; the
-- _5v5 columns cover 5-on-5 with both goalies in.

{{ config(materialized='table', tags=['advanced', 'xg']) }}

select
    season || '-' || game_type || '-' || shooting_player_id as skater_season_key,
    shooting_player_id as player_id,
    season,
    game_type,
    count(*) as unblocked_attempts,
    count(*) filter (where is_on_goal_or_goal) as shots_on_goal,
    count(*) filter (where is_goal) as goals,
    sum(xg) as xg,
    count(*) filter (where is_goal) - sum(xg) as goals_above_expected,
    sum(xg) / count(*) as xg_per_attempt,
    count(*) filter (where is_5v5) as unblocked_attempts_5v5,
    count(*) filter (where is_5v5 and is_goal) as goals_5v5,
    coalesce(sum(xg) filter (where is_5v5), 0) as xg_5v5
from (
    select *, event_type in ('goal', 'shot-on-goal') as is_on_goal_or_goal
    from {{ ref('fct_shot_xg') }}
    where shooting_player_id is not null
)
group by season, game_type, shooting_player_id
