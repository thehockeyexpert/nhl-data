-- A warning, not a failure: lists finished seasons where teams did not all play the
-- scheduled number of games, so the games-per-team check was skipped for them.
{{ config(severity='warn') }}

with team_games as (

    select season, home_team_id as team_id
    from {{ ref('fct_games') }}
    where game_type_label = 'regular'
    union all
    select season, away_team_id
    from {{ ref('fct_games') }}
    where game_type_label = 'regular'

),

team_counts as (

    select season, count(distinct team_id) as teams
    from team_games
    group by season

)

select
    seasons.season,
    team_counts.teams,
    seasons.scheduled_games_per_team,
    seasons.total_regular_season_games
from {{ ref('stg_nhl_stats__seasons') }} as seasons
inner join team_counts on team_counts.season = seasons.season
where seasons.season_end_date < current_date
  and seasons.total_regular_season_games * 2 != team_counts.teams * seasons.scheduled_games_per_team
