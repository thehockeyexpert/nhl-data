-- Which teams a skater played for in a season and game type: one row per team in the API's team list.
-- The totals in fct_skater_seasons are not split by team, so this table holds no statistics.
-- An abbreviation is matched to the team that used it in that season's regular-season and playoff games;
-- team_id is empty if no team used it (check skater_team_resolves).

with skater_seasons as (

    select * from {{ ref('stg_nhl_stats__skater_seasons') }}

),

listed as (

    -- distinct: a player who left a team and came back has that team listed twice (observed 15 times).
    select distinct
        skater_season_key,
        player_id,
        season,
        game_type,
        trim(unnest(string_split(team_abbrevs, ','))) as team_abbrev
    from skater_seasons
    where team_abbrevs is not null and team_abbrevs != ''

),

season_abbrevs as (

    -- Each abbreviation a team used in a season's games.
    select distinct season, home_team_abbrev as team_abbrev, home_team_id as team_id
    from {{ ref('fct_games') }}
    where game_type in (2, 3)
    union
    select distinct season, away_team_abbrev, away_team_id
    from {{ ref('fct_games') }}
    where game_type in (2, 3)

)

select
    listed.skater_season_key || '-' || listed.team_abbrev as skater_season_team_key,
    listed.skater_season_key,
    listed.player_id,
    listed.season,
    listed.game_type,
    listed.team_abbrev,
    season_abbrevs.team_id
from listed
left join season_abbrevs
    on season_abbrevs.season = listed.season
    and season_abbrevs.team_abbrev = listed.team_abbrev
