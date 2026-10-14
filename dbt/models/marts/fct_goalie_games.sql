-- One row per goalie per game (regular season and playoffs), linked to fct_games.
-- The stats API gives a team abbreviation but no team ID, and abbreviations are reused across eras,
-- so the team comes from the game: the home team if the goalie's row is H, otherwise the away team.

with goalie_games as (

    select * from {{ ref('stg_nhl_stats__goalie_games') }}

),

games as (

    select * from {{ ref('fct_games') }}

)

select
    goalie_games.goalie_game_key,
    goalie_games.game_id,
    goalie_games.season,
    goalie_games.game_type,
    games.game_type_label,
    games.game_date,
    goalie_games.player_id,
    goalie_games.goalie_name,
    goalie_games.home_road = 'H' as is_home,
    case when goalie_games.home_road = 'H' then games.home_team_id else games.away_team_id end as team_id,
    case when goalie_games.home_road = 'H' then games.away_team_id else games.home_team_id end as opponent_team_id,
    goalie_games.team_abbrev,
    goalie_games.games_started = 1 as is_starter,
    -- The credited decision (D04). Empty when the goalie got no decision in that game.
    case
        when goalie_games.wins > 0 then 'W'
        when goalie_games.ties > 0 then 'T'
        when goalie_games.ot_losses > 0 then 'OTL'
        when goalie_games.losses > 0 then 'L'
    end as decision,
    goalie_games.shutouts > 0 as is_shutout,
    goalie_games.goals_against,
    goalie_games.shots_against,
    goalie_games.saves,
    goalie_games.time_on_ice_seconds,
    goalie_games.goals,
    goalie_games.assists,
    goalie_games.penalty_minutes
from goalie_games
left join games on games.game_id = goalie_games.game_id
