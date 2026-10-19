-- One row per team per season from the NHL's standings on the season's first standings day: the team's
-- conference and division that season. Empty where the season had no conferences or divisions.
-- The standings name each team by abbreviation only; dim_team_season matches it to a team_id.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_web__standings') }}
    qualify row_number() over (partition by season order by loaded_at desc) = 1

),

teams as (

    select season, unnest(json_extract(payload, '$.standings[*]')) as team
    from latest_response

)

select
    season || '-' || (team -> '$.teamAbbrev' ->> 'default') as team_season_abbrev_key,
    season,
    team -> '$.teamAbbrev' ->> 'default' as team_abbrev,
    team -> '$.teamName' ->> 'default' as team_name,
    team ->> 'conferenceName' as conference_name,
    team ->> 'conferenceAbbrev' as conference_abbrev,
    team ->> 'divisionName' as division_name,
    team ->> 'divisionAbbrev' as division_abbrev
from teams
