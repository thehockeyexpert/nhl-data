-- One row per team per game, regular season and playoffs, from the NHL stats API's team power-play report (isGame=true).
{{ config(materialized='incremental', unique_key='team_game_key', incremental_strategy='delete+insert') }}

{{ team_game_report('nhl_stats__team_game_powerplay', [
    ['powerPlayGoalsFor', 'power_play_goals', 'integer'],
    ['ppOpportunities', 'power_play_opportunities', 'integer'],
    ['ppTimeOnIcePerGame', 'power_play_seconds', 'double'],
    ['shGoalsAgainst', 'short_handed_goals_against', 'integer'],
]) }}
