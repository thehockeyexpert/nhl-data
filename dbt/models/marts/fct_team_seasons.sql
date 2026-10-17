-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- One row per team per regular season: the NHL's official season totals, from the NHL stats API.
-- These are the NHL's own numbers, not totals of our games; check team_season_goals_match_games compares them.
-- Shots per game exist from 1959-60.

select
    team_season_key,
    season,
    team_id,
    team_name,
    games_played,
    wins,
    losses,
    ties,
    ot_losses,
    points,
    points / nullif(2.0 * games_played, 0) as points_pct,
    goals_for,
    goals_against,
    goals_for - goals_against as goal_difference,
    shots_for_per_game,
    shots_against_per_game,
    team_shutouts
from {{ ref('stg_nhl_stats__team_seasons') }}
