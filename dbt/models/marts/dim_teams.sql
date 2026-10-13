-- One row per team identity that appears in our games.
-- NHL teams carry two groupings: the NHL's official franchise, and a lineage that follows
-- the club through its moves. The two are the same unless seeds/team_lineage_overrides.csv says otherwise.

with nhl_teams as (

    -- The NHL team list also holds two placeholders with no franchise ("To be determined", "NHL").
    select *
    from {{ ref('stg_nhl_stats__teams') }}
    where franchise_id is not null

),

team_spans as (

    select
        team_id,
        min(first_season) as first_season,
        -- An empty last season means the team is still playing.
        case when bool_or(last_season is null) then null else max(last_season) end as last_season,
        bool_or(is_active_team) as is_active
    from {{ ref('stg_nhl_records__franchise_team_totals') }}
    group by team_id

),

franchises as (

    select franchise_id, franchise_name
    from {{ ref('stg_nhl_records__franchises') }}

),

nhl as (

    select
        nhl_teams.team_id,
        nhl_teams.team_name,
        nhl_teams.team_abbrev,
        true as is_nhl_team,
        team_spans.first_season,
        team_spans.last_season,
        coalesce(team_spans.is_active, false) as is_active,
        nhl_teams.franchise_id,
        franchises.franchise_name,
        coalesce(overrides.lineage_id, nhl_teams.franchise_id) as lineage_id
    from nhl_teams
    left join team_spans on team_spans.team_id = nhl_teams.team_id
    left join franchises on franchises.franchise_id = nhl_teams.franchise_id
    left join {{ ref('team_lineage_overrides') }} as overrides on overrides.team_id = nhl_teams.team_id

),

game_teams as (

    select season, home_team_id as team_id, home_team_name as team_name, home_team_abbrev as team_abbrev
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (1, 2, 3)
    union all
    select season, away_team_id, away_team_name, away_team_abbrev
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (1, 2, 3)

),

other_opponents as (

    -- Opponents that are not in the NHL team list, such as early Stanley Cup challengers
    -- from other leagues. All we know about them comes from the games themselves.
    select
        team_id,
        mode(team_name) as team_name,
        mode(team_abbrev) as team_abbrev,
        min(season) as first_season,
        max(season) as last_season
    from game_teams
    where team_id not in (select team_id from nhl_teams)
    group by team_id

)

select
    nhl.team_id,
    nhl.team_name,
    nhl.team_abbrev,
    nhl.is_nhl_team,
    nhl.first_season,
    nhl.last_season,
    nhl.is_active,
    nhl.franchise_id,
    nhl.franchise_name,
    nhl.lineage_id,
    lineage_franchises.franchise_name as lineage_name
from nhl
left join franchises as lineage_franchises on lineage_franchises.franchise_id = nhl.lineage_id

union all

select
    team_id,
    team_name,
    team_abbrev,
    false as is_nhl_team,
    first_season,
    last_season,
    null as is_active,
    null as franchise_id,
    null as franchise_name,
    null as lineage_id,
    null as lineage_name
from other_opponents
