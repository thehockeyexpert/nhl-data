-- One row per game, unpacked from the weekly schedule responses.

with latest_responses as (

    -- If a week was downloaded more than once, keep only the newest copy.
    select *
    from {{ source('raw', 'nhl_web__schedule') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

days as (

    -- Each response holds a list of days.
    select
        loaded_at,
        unnest(json_extract(payload, '$.gameWeek[*]')) as day
    from latest_responses

),

games as (

    -- Each day holds a list of games.
    select
        loaded_at,
        (day ->> 'date')::date as game_date,
        unnest(json_extract(day, '$.games[*]')) as game
    from days

),

renamed as (

    select
        (game ->> 'id')::bigint as game_id,
        (game ->> 'season')::integer as season,
        (game ->> 'gameType')::integer as game_type,
        game_date,
        (game ->> 'startTimeUTC')::timestamptz as start_time_utc,
        (game -> 'homeTeam' ->> 'id')::integer as home_team_id,
        game -> 'homeTeam' ->> 'abbrev' as home_team_abbrev,
        -- Place plus name ("Florida Panthers"), unless the name already holds the place or there is none
        -- (all-star and national teams give e.g. place "Pacific" and name "Pacific").
        case
            when coalesce(game -> 'homeTeam' -> 'placeName' ->> 'default', '') = ''
                or contains(game -> 'homeTeam' -> 'commonName' ->> 'default', game -> 'homeTeam' -> 'placeName' ->> 'default')
                then game -> 'homeTeam' -> 'commonName' ->> 'default'
            else (game -> 'homeTeam' -> 'placeName' ->> 'default') || ' ' || (game -> 'homeTeam' -> 'commonName' ->> 'default')
        end as home_team_name,
        (game -> 'homeTeam' ->> 'score')::integer as home_score,
        (game -> 'awayTeam' ->> 'id')::integer as away_team_id,
        game -> 'awayTeam' ->> 'abbrev' as away_team_abbrev,
        -- Place plus name ("Florida Panthers"), unless the name already holds the place or there is none
        -- (all-star and national teams give e.g. place "Pacific" and name "Pacific").
        case
            when coalesce(game -> 'awayTeam' -> 'placeName' ->> 'default', '') = ''
                or contains(game -> 'awayTeam' -> 'commonName' ->> 'default', game -> 'awayTeam' -> 'placeName' ->> 'default')
                then game -> 'awayTeam' -> 'commonName' ->> 'default'
            else (game -> 'awayTeam' -> 'placeName' ->> 'default') || ' ' || (game -> 'awayTeam' -> 'commonName' ->> 'default')
        end as away_team_name,
        (game -> 'awayTeam' ->> 'score')::integer as away_score,
        game ->> 'gameState' as game_state,
        game ->> 'gameScheduleState' as game_schedule_state,
        -- How the game ended: REG (regulation), OT (overtime) or SO (shootout).
        game -> 'gameOutcome' ->> 'lastPeriodType' as last_period_type,
        game -> 'venue' ->> 'default' as venue_name,
        (game ->> 'neutralSite')::boolean as is_neutral_site,
        loaded_at
    from games
    -- A game can show up in more than one response. Keep the newest.
    qualify row_number() over (partition by game_id order by loaded_at desc) = 1

)

select
    renamed.game_id,
    renamed.season,
    renamed.game_type,
    -- Only verified (season, game type) pairs have a label. See seeds/game_type_labels.csv.
    coalesce(
        season_labels.label,
        all_season_labels.label,
        'unknown type ' || renamed.game_type::varchar
    ) as game_type_label,
    renamed.game_date,
    renamed.start_time_utc,
    renamed.home_team_id,
    renamed.home_team_abbrev,
    renamed.home_team_name,
    renamed.home_score,
    renamed.away_team_id,
    renamed.away_team_abbrev,
    renamed.away_team_name,
    renamed.away_score,
    renamed.game_state,
    renamed.game_schedule_state,
    -- The API marks finished games as FINAL at first and OFF (official) later.
    renamed.game_state in ('FINAL', 'OFF') as is_final,
    renamed.last_period_type,
    renamed.venue_name,
    renamed.is_neutral_site,
    renamed.loaded_at
from renamed
left join {{ ref('game_type_labels') }} as season_labels
    on season_labels.season = renamed.season
    and season_labels.game_type = renamed.game_type
left join {{ ref('game_type_labels') }} as all_season_labels
    on all_season_labels.season is null
    and all_season_labels.game_type = renamed.game_type
