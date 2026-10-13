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
        (game -> 'homeTeam' ->> 'score')::integer as home_score,
        (game -> 'awayTeam' ->> 'id')::integer as away_team_id,
        game -> 'awayTeam' ->> 'abbrev' as away_team_abbrev,
        (game -> 'awayTeam' ->> 'score')::integer as away_score,
        game ->> 'gameState' as game_state,
        game ->> 'gameScheduleState' as game_schedule_state,
        -- How the game ended: REG (regulation), OT (overtime) or SO (shootout).
        game -> 'gameOutcome' ->> 'lastPeriodType' as last_period_type,
        game -> 'venue' ->> 'default' as venue_name,
        (game ->> 'neutralSite')::boolean as is_neutral_site,
        loaded_at
    from games

)

select
    game_id,
    season,
    game_type,
    {{ game_type_label('season', 'game_type') }} as game_type_label,
    game_date,
    start_time_utc,
    home_team_id,
    home_team_abbrev,
    home_score,
    away_team_id,
    away_team_abbrev,
    away_score,
    game_state,
    game_schedule_state,
    -- The API marks finished games as FINAL at first and OFF (official) later.
    game_state in ('FINAL', 'OFF') as is_final,
    last_period_type,
    venue_name,
    is_neutral_site,
    loaded_at
from renamed
-- A game can show up in more than one response. Keep the newest.
qualify row_number() over (partition by game_id order by loaded_at desc) = 1
