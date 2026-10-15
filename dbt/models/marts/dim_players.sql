-- One row per person in the NHL's player list, plus anyone who appears in our skater or goalie stats but not in it.
-- is_nhl_player (D15): at least one regular-season or playoff game, as a skater (a season with games played above 0)
-- or as a goalie (a goalie game). The player list also holds people who never played an NHL game.
-- Birthplace is as the NHL records it (D14).

with players as (

    select * from {{ ref('stg_nhl_records__players') }}

),

skater_seasons as (

    select player_id, season, skater_name as player_name, position_code
    from {{ ref('fct_skater_seasons') }}
    where game_type in (2, 3) and games_played > 0

),

goalie_seasons as (

    select distinct player_id, season, goalie_name as player_name, 'G' as position_code
    from {{ ref('fct_goalie_games') }}
    where game_type in (2, 3)

),

nhl_seasons as (

    select * from skater_seasons
    union all
    select * from goalie_seasons

),

nhl_careers as (

    select
        player_id,
        min(season) as first_nhl_season,
        max(season) as last_nhl_season,
        arg_max(player_name, season) as latest_name,
        arg_max(position_code, season) as latest_position
    from nhl_seasons
    group by player_id

)

select
    coalesce(players.player_id, nhl_careers.player_id) as player_id,
    coalesce(players.full_name, nhl_careers.latest_name) as full_name,
    players.first_name,
    players.last_name,
    coalesce(players.position, nhl_careers.latest_position) as position,
    players.shoots_catches,
    players.birth_date,
    players.birth_city,
    players.birth_state_province,
    players.birth_country,
    players.nationality,
    players.height_inches,
    players.weight_pounds,
    players.is_deceased,
    players.hall_of_fame_year,
    nhl_careers.player_id is not null as is_nhl_player,
    nhl_careers.first_nhl_season,
    nhl_careers.last_nhl_season,
    players.player_id is not null as is_in_player_list
from players
full outer join nhl_careers on nhl_careers.player_id = players.player_id
