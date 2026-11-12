-- One row per player, season, league, team and game type, in every league the NHL's player pages list: junior,
-- college, minor and major pro, international tournaments and the NHL itself (decided 2026-11-11).
-- Use it for players' paths: where someone played before, during and after their NHL career.
-- For NHL seasons, fct_skater_seasons and fct_goalie_games remain the main source; the NHL rows here are what the
-- player page shows. Not rebuilt nightly (tag player_pages): the pages are refreshed by hand.

{{ config(tags=['player_pages']) }}

with season_totals as (

    select * from {{ ref('stg_nhl_web__player_season_totals') }}

),

players as (

    select player_id, full_name, first_nhl_season
    from {{ ref('dim_players') }}

)

select
    season_totals.season_total_key,
    season_totals.player_id,
    players.full_name,
    season_totals.season,
    season_totals.game_type,
    season_totals.league_abbrev,
    season_totals.league_abbrev = 'NHL' as is_nhl,
    season_totals.sequence,
    season_totals.team_name,
    players.first_nhl_season,
    season_totals.season < players.first_nhl_season as is_before_first_nhl_season,
    season_totals.games_played,
    season_totals.goals,
    season_totals.assists,
    season_totals.points,
    season_totals.penalty_minutes,
    season_totals.plus_minus,
    season_totals.power_play_goals,
    season_totals.power_play_points,
    season_totals.shorthanded_goals,
    season_totals.shorthanded_points,
    season_totals.game_winning_goals,
    season_totals.ot_goals,
    season_totals.shots,
    season_totals.shooting_pct,
    season_totals.faceoff_win_pct,
    season_totals.avg_toi_seconds,
    season_totals.games_started,
    season_totals.wins,
    season_totals.losses,
    season_totals.ties,
    season_totals.ot_losses,
    season_totals.shutouts,
    season_totals.goals_against,
    season_totals.shots_against,
    season_totals.goals_against_avg,
    season_totals.save_pct,
    season_totals.time_on_ice_seconds
from season_totals
left join players using (player_id)
