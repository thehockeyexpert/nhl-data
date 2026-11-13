-- One row per team per game, regular season and playoffs, from the NHL stats API's team penalty-kill report (isGame=true).
{{ config(materialized='incremental', unique_key='team_game_key', incremental_strategy='delete+insert') }}

{{ team_game_report('nhl_stats__team_game_penaltykill', [
    ['timesShorthanded', 'times_short_handed', 'integer'],
    ['ppGoalsAgainst', 'power_play_goals_against', 'integer'],
    ['shGoalsFor', 'short_handed_goals', 'integer'],
    ['pkTimeOnIcePerGame', 'short_handed_seconds', 'double'],
]) }}
