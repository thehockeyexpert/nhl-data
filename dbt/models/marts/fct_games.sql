-- One row per NHL game: preseason, regular season and playoffs.
-- Special events such as the Olympics are left out.

with games as (

    select *
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (1, 2, 3)

)

select
    game_id,
    season,
    game_type,
    game_type_label,
    game_date,
    start_time_utc,
    home_team_id,
    home_team_abbrev,
    away_team_id,
    away_team_abbrev,
    home_score,
    away_score,
    is_final,
    last_period_type,
    case
        when not is_final then null
        when home_score > away_score then home_team_id
        when away_score > home_score then away_team_id
    end as winner_team_id,
    case
        when not is_final then null
        when home_score > away_score then home_team_abbrev
        when away_score > home_score then away_team_abbrev
    end as winner_team_abbrev,
    is_final and home_score = away_score as is_tie,
    venue_name,
    is_neutral_site
from games
