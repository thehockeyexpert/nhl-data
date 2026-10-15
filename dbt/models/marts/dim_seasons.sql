-- One row per season the NHL has season facts for (2004-05 has none; it was not played).
-- Combines the NHL's season facts, its standings rules for the season, and whether our checks treat it as finished.

with seasons as (

    select * from {{ ref('stg_nhl_stats__seasons') }}

),

rules as (

    select * from {{ ref('stg_nhl_web__standings_rules') }}

),

status as (

    select season, is_finished from {{ ref('season_status') }}

),

teams as (

    select season, count(distinct team_id) as regular_season_teams
    from {{ ref('fct_team_games') }}
    where game_type = 2
    group by season

)

select
    seasons.season,
    seasons.season_label,
    seasons.season // 10000 as start_year,
    seasons.regular_season_start_date,
    seasons.regular_season_end_date,
    seasons.season_end_date,
    seasons.scheduled_games_per_team,
    seasons.total_regular_season_games,
    seasons.total_playoff_games,
    teams.regular_season_teams,
    seasons.is_ties_in_use,
    rules.is_point_for_ot_loss_in_use,
    seasons.season >= 20052006 as is_shootout_in_use,
    rules.is_regulation_wins_in_use,
    rules.is_row_in_use,
    status.is_finished
from seasons
left join rules on rules.season = seasons.season
left join status on status.season = seasons.season
left join teams on teams.season = seasons.season
