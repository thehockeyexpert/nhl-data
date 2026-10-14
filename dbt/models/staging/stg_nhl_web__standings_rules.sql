-- One row per season with the standings rules the NHL used that season.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_web__standings_season') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

seasons as (

    select unnest(json_extract(payload, '$.seasons[*]')) as season_rules
    from latest_response

)

select
    (season_rules ->> 'id')::integer as season,
    (season_rules ->> 'standingsStart')::date as standings_start_date,
    (season_rules ->> 'standingsEnd')::date as standings_end_date,
    (season_rules ->> 'tiesInUse')::boolean as is_ties_in_use,
    (season_rules ->> 'pointForOTlossInUse')::boolean as is_point_for_ot_loss_in_use,
    (season_rules ->> 'regulationWinsInUse')::boolean as is_regulation_wins_in_use,
    (season_rules ->> 'rowInUse')::boolean as is_row_in_use,
    (season_rules ->> 'wildcardInUse')::boolean as is_wildcard_in_use,
    (season_rules ->> 'conferencesInUse')::boolean as is_conferences_in_use,
    (season_rules ->> 'divisionsInUse')::boolean as is_divisions_in_use
from seasons
