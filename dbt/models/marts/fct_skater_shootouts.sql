-- One row per skater per regular season with at least one shootout attempt, 2005-06 onward. Success rate is
-- goals / attempts; sum both over seasons before dividing for a career rate. Agreed minimums (2026-11-11): 5 attempts
-- for a season, 25 for a career.

select
    skater_shootout_key,
    player_id,
    season,
    skater_name,
    team_abbrevs,
    shootout_games,
    shootout_attempts,
    shootout_goals,
    shootout_deciding_goals,
    shootout_goals::double / nullif(shootout_attempts, 0) as shootout_success_pct
from {{ ref('stg_nhl_stats__skater_shootouts') }}
where shootout_attempts > 0  -- the report also lists skaters who took no attempt
