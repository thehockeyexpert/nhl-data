-- One row per season: the NHL's own facts about it.
-- The data checks compare our game counts against these numbers.

with latest_responses as (

    select *
    from {{ source('raw', 'nhl_stats__season') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

seasons as (

    select
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as season
    from latest_responses

)

select
    (season ->> 'id')::integer as season,
    season ->> 'formattedSeasonId' as season_label,
    (season ->> 'numberOfGames')::integer as scheduled_games_per_team,
    (season ->> 'totalRegularSeasonGames')::integer as total_regular_season_games,
    (season ->> 'totalPlayoffGames')::integer as total_playoff_games,
    (season ->> 'tiesInUse')::integer = 1 as is_ties_in_use,
    (season ->> 'startDate')::timestamp::date as regular_season_start_date,
    (season ->> 'regularSeasonEndDate')::timestamp::date as regular_season_end_date,
    (season ->> 'endDate')::timestamp::date as season_end_date,
    loaded_at
from seasons
qualify row_number() over (partition by (season ->> 'id') order by loaded_at desc) = 1
