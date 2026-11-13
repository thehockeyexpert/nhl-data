-- One row per team per game, regular season and playoffs, from the NHL stats API's team penalties report (isGame=true).
{{ config(materialized='incremental', unique_key='team_game_key', incremental_strategy='delete+insert') }}

{{ team_game_report('nhl_stats__team_game_penalties', [
    ['penaltyMinutes', 'penalty_minutes', 'integer'],
    ['penalties', 'penalties', 'integer'],
    ['minors', 'minors', 'integer'],
    ['majors', 'majors', 'integer'],
    ['misconducts', 'misconducts', 'integer'],
    ['gameMisconducts', 'game_misconducts', 'integer'],
    ['matchPenalties', 'match_penalties', 'integer'],
    ['benchMinorPenalties', 'bench_minors', 'integer'],
    ['totalPenaltiesDrawn', 'penalties_drawn', 'integer'],
]) }}
