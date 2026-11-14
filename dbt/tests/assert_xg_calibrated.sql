-- Our expected-goals model (docs/definitions.md, D33): in every finished season from 2010-11, total xG is within 2% of
-- the actual goals (unblocked shots, shootouts left out). A WARNING, not an error: a season outside 2% means the
-- model drifts for that era (shot recording or scoring changed), which is worth knowing but does not make the data
-- wrong. Returns one row per season outside 2%.
{{ config(severity='warn') }}

with seasons as (

    select season, count(*) filter (where is_goal) as goals, sum(xg) as xg
    from {{ ref('fct_shot_xg') }}
    where season in (select season from {{ ref('season_status') }} where is_finished)
    group by season

)

select season, goals, round(xg, 1) as xg, round(100.0 * (xg / goals - 1), 2) as xg_minus_goals_pct
from seasons
where abs(xg / goals - 1) > 0.02
