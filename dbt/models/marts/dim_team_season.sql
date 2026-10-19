-- One row per team per regular season, from 1917-18 to the current season: the team's conference and division,
-- from the NHL's standings. The standings name teams by abbreviation, which the NHL reuses across eras, so each one
-- is matched to a team_id through that season's regular-season games (one team per abbreviation per season).
-- Where the abbreviation differs from the games' (the Cleveland Barons are CBN in the standings, CLE in the games),
-- the team's full name that season is used instead. Names are also unique within a season.

with standings as (

    select * from {{ ref('stg_nhl_web__standings') }}

),

season_teams as (

    select distinct season, home_team_id as team_id, home_team_abbrev as team_abbrev, home_team_name as team_name
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type = 2
    union
    select distinct season, away_team_id, away_team_abbrev, away_team_name
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type = 2

),

rules as (

    select season, is_conferences_in_use, is_divisions_in_use
    from {{ ref('stg_nhl_web__standings_rules') }}

)

select
    standings.season || '-' || coalesce(by_abbrev.team_id, by_name.team_id) as team_season_key,
    coalesce(by_abbrev.team_id, by_name.team_id) as team_id,
    standings.season,
    standings.team_abbrev,
    standings.team_name,
    standings.conference_name,
    standings.division_name,
    rules.is_conferences_in_use,
    rules.is_divisions_in_use
from standings
left join season_teams as by_abbrev
    on by_abbrev.season = standings.season
   and by_abbrev.team_abbrev = standings.team_abbrev
left join season_teams as by_name
    on by_name.season = standings.season
   and by_name.team_name = standings.team_name
left join rules on rules.season = standings.season
