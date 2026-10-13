-- One row per team identity in the NHL's team list, with the franchise it belongs to.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_stats__team') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

teams as (

    select unnest(json_extract(payload, '$.data[*]')) as team
    from latest_response

)

select
    (team ->> 'id')::integer as team_id,
    (team ->> 'franchiseId')::integer as franchise_id,
    team ->> 'fullName' as team_name,
    team ->> 'triCode' as team_abbrev,
    (team ->> 'leagueId')::integer as league_id
from teams
