-- One row per team per game, regular season and playoffs, from the NHL stats API's team summary (isGame=true).
{{ config(materialized='incremental', unique_key='team_game_key', incremental_strategy='delete+insert') }}

{{ team_game_report('nhl_stats__team_game_summary', [
    ['goalsFor', 'goals_for', 'integer'],
    ['goalsAgainst', 'goals_against', 'integer'],
    ['wins', 'wins', 'integer'],
    ['losses', 'losses', 'integer'],
    ['otLosses', 'ot_losses', 'integer'],
    ['ties', 'ties', 'integer'],
    ['points', 'points', 'integer'],
    ['shotsForPerGame', 'shots_for', 'integer'],
    ['shotsAgainstPerGame', 'shots_against', 'integer'],
    ['faceoffWinPct', 'faceoff_win_pct', 'double'],
    ['powerPlayPct', 'power_play_pct', 'double'],
    ['penaltyKillPct', 'penalty_kill_pct', 'double'],
]) }}
