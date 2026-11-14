-- One row per team per regular season from 2010-11: expected goals for and against (our model, docs/definitions.md
-- D33), xGF%, and actual non-shootout goals beside them, in all situations and at 5-on-5. Summed from fct_team_game_xg.

{{ config(materialized='table', tags=['advanced', 'xg']) }}

with totals as (

    select
        season,
        team_id,
        count(*) as games_played,
        sum(xgf) as xgf,
        sum(xga) as xga,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        sum(xgf_5v5) as xgf_5v5,
        sum(xga_5v5) as xga_5v5,
        sum(goals_for_5v5) as goals_for_5v5,
        sum(goals_against_5v5) as goals_against_5v5
    from {{ ref('fct_team_game_xg') }}
    where game_type = 2
    group by season, team_id

)

select
    season || '-' || team_id as team_season_key,
    *,
    xgf / nullif(xgf + xga, 0) as xgf_pct,
    xgf_5v5 / nullif(xgf_5v5 + xga_5v5, 0) as xgf_pct_5v5,
    goals_for - xgf as goals_for_above_expected,
    xga - goals_against as goals_against_below_expected
from totals
