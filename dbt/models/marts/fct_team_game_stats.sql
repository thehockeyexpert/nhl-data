-- One row per team per finished regular-season or playoff game: power play, penalty kill, penalties and shots, from
-- the NHL stats API's per-game team reports. Built on fct_team_games, so teams, results and keys match the games
-- tables; a game the reports leave out keeps its row with empty stats (checked by team_game_stats_covered).
-- Empty means not recorded, never zero: power-play opportunities and times short-handed from 1977-78, shots from
-- 1959-60, power-play and short-handed time from 1997-98 (docs/data_coverage.md, "Team game statistics").
-- Before 1977-78 the NHL's opportunity fields hold a few stray values (37 in all, against 495 power-play goals
-- before 1933), so they are left empty there. The report's goals leave out the shootout goal the final score adds.

{{ config(materialized='table', tags=['team_games']) }}

with team_games as (

    select * from {{ ref('fct_team_games') }}

),

summary as (

    select * from {{ ref('stg_nhl_stats__team_game_summary') }}

),

powerplay as (

    select * from {{ ref('stg_nhl_stats__team_game_powerplay') }}

),

penaltykill as (

    select * from {{ ref('stg_nhl_stats__team_game_penaltykill') }}

),

penalties as (

    select * from {{ ref('stg_nhl_stats__team_game_penalties') }}

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
    team_games.goals_for,
    team_games.goals_against,
    team_games.result,
    summary.shots_for,
    summary.shots_against,
    powerplay.power_play_goals,
    case when team_games.season >= 19771978 then powerplay.power_play_opportunities end as power_play_opportunities,
    powerplay.power_play_seconds,
    powerplay.short_handed_goals_against,
    case when team_games.season >= 19771978 then penaltykill.times_short_handed end as times_short_handed,
    penaltykill.power_play_goals_against,
    penaltykill.short_handed_goals,
    penaltykill.short_handed_seconds,
    penalties.penalty_minutes,
    penalties.penalties,
    penalties.minors,
    penalties.majors,
    penalties.misconducts,
    penalties.game_misconducts,
    penalties.match_penalties,
    penalties.bench_minors,
    penalties.penalties_drawn,
    summary.faceoff_win_pct,
    summary.goals_for as stats_goals_for,
    summary.goals_against as stats_goals_against,
    summary.game_id is not null as has_team_stats
from team_games
left join summary
    on summary.game_id = team_games.game_id and summary.team_id = team_games.team_id
left join powerplay
    on powerplay.game_id = team_games.game_id and powerplay.team_id = team_games.team_id
left join penaltykill
    on penaltykill.game_id = team_games.game_id and penaltykill.team_id = team_games.team_id
left join penalties
    on penalties.game_id = team_games.game_id and penalties.team_id = team_games.team_id
where team_games.game_type in (2, 3)
