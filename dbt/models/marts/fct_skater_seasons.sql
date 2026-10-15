-- One row per skater per season and game type (2 regular season, 3 playoffs), with season totals.
-- The stats API gives the teams as abbreviations ("TOR,BOS" for a player who changed teams) and does not split
-- the totals by team. Abbreviations are reused across eras, so each one is matched to the team that used it in
-- that season's games. team_id is filled only when the player had one team that season; all teams are listed in
-- bridge_skater_season_teams.

with skater_seasons as (

    select * from {{ ref('stg_nhl_stats__skater_seasons') }}

),

season_teams as (

    select * from {{ ref('bridge_skater_season_teams') }}

),

team_counts as (

    select
        skater_season_key,
        count(*) as team_count,
        any_value(team_id) as only_team_id
    from season_teams
    group by skater_season_key

),

labels as (

    select season, game_type, label from {{ ref('game_type_labels') }}

)

select
    skater_seasons.skater_season_key,
    skater_seasons.player_id,
    skater_seasons.season,
    skater_seasons.game_type,
    labels.label as game_type_label,
    skater_seasons.skater_name,
    skater_seasons.position_code,
    case when team_counts.team_count = 1 then team_counts.only_team_id end as team_id,
    team_counts.team_count,
    skater_seasons.team_abbrevs,
    skater_seasons.games_played,
    skater_seasons.goals,
    skater_seasons.assists,
    skater_seasons.points,
    skater_seasons.plus_minus,
    skater_seasons.penalty_minutes,
    skater_seasons.even_strength_goals,
    skater_seasons.even_strength_points,
    skater_seasons.power_play_goals,
    skater_seasons.power_play_points,
    skater_seasons.short_handed_goals,
    skater_seasons.short_handed_points,
    skater_seasons.game_winning_goals,
    skater_seasons.overtime_goals,
    skater_seasons.shots,
    skater_seasons.time_on_ice_per_game_seconds,
    skater_seasons.faceoff_win_pct
from skater_seasons
left join team_counts on team_counts.skater_season_key = skater_seasons.skater_season_key
left join labels on labels.season = skater_seasons.season and labels.game_type = skater_seasons.game_type
