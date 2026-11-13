-- One row per team per home era: the city and building where the team played most of its regular-season home games,
-- with consecutive seasons in the same building merged. Built from the games and our venues seed, not hand-written, so
-- a move or a new arena appears by itself. Neutral-site "home" games (Global Series, early barnstorming games) never
-- decide the home building unless they are the majority. The city is the building's municipality as in the venues seed
-- (Inglewood for the Forum, Uniondale for Nassau Coliseum). Coordinates are the building's, for travel distances.

with home_games as (

    select
        games.season,
        games.home_team_id as team_id,
        venues.building_id,
        count(*) as games
    from {{ ref('fct_games') }} as games
    inner join {{ ref('venues') }} as venues on venues.venue_name = games.venue_name
    where games.game_type = 2
      and games.is_final
    group by all

),

main_building as (

    -- The building with the most home games that season (ties broken by building_id, so the result is stable).
    select
        season,
        team_id,
        building_id,
        games as main_building_games,
        sum(games) over (partition by season, team_id) as home_games
    from home_games
    qualify row_number() over (partition by season, team_id order by games desc, building_id) = 1

),

eras as (

    -- Gaps and islands: consecutive seasons of the same team in the same building form one era.
    select
        *,
        row_number() over (partition by team_id order by season)
            - row_number() over (partition by team_id, building_id order by season) as era_group
    from main_building

),

buildings as (

    select
        building_id,
        any_value(building_name) as building_name,
        any_value(city) as city,
        any_value(country) as country,
        any_value(latitude) as latitude,
        any_value(longitude) as longitude
    from {{ ref('venues') }}
    group by building_id

)

select
    eras.team_id || '-' || min(eras.season) as home_era_key,
    eras.team_id,
    any_value(teams.team_name) as team_name,
    min(eras.season) as from_season,
    max(eras.season) as to_season,
    count(*) as seasons,
    any_value(buildings.city) as home_city,
    any_value(buildings.country) as country,
    eras.building_id,
    any_value(buildings.building_name) as building_name,
    any_value(buildings.latitude) as latitude,
    any_value(buildings.longitude) as longitude,
    sum(eras.home_games) as home_games,
    sum(eras.main_building_games) as main_building_games,
    count(*) filter (where eras.main_building_games < 0.6 * eras.home_games) as split_seasons
from eras
inner join buildings on buildings.building_id = eras.building_id
left join {{ ref('dim_teams') }} as teams on teams.team_id = eras.team_id
group by eras.team_id, eras.building_id, eras.era_group
