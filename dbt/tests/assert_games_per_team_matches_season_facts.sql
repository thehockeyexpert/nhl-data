-- In a balanced season every team plays the scheduled number of games.
-- A season is balanced when total games = teams x games per team / 2.
-- Seasons that were cut short (2019-20) are not balanced and are skipped here;
-- warn_season_not_balanced reports them instead.
-- Returns the teams whose game count is wrong.

with team_games as (

    select season, home_team_id as team_id, home_team_abbrev as team_abbrev
    from {{ ref('fct_games') }}
    where game_type_label = 'regular'
    union all
    select season, away_team_id, away_team_abbrev
    from {{ ref('fct_games') }}
    where game_type_label = 'regular'

),

per_team as (

    select season, team_id, any_value(team_abbrev) as team_abbrev, count(*) as games
    from team_games
    group by season, team_id

),

team_counts as (

    select season, count(*) as teams
    from per_team
    group by season

),

balanced_seasons as (

    select seasons.season, seasons.scheduled_games_per_team
    from {{ ref('stg_nhl_stats__seasons') }} as seasons
    inner join team_counts on team_counts.season = seasons.season
    where seasons.season_end_date < current_date
      and seasons.total_regular_season_games * 2 = team_counts.teams * seasons.scheduled_games_per_team

)

select
    per_team.season,
    per_team.team_abbrev,
    balanced_seasons.scheduled_games_per_team as expected_games,
    per_team.games as actual_games
from per_team
inner join balanced_seasons on balanced_seasons.season = per_team.season
where per_team.games != balanced_seasons.scheduled_games_per_team
