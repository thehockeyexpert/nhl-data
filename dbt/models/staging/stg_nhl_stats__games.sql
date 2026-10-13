-- One row per game, unpacked from the stats API game list.
-- This is the thinner, independent source used to cross-check the weekly schedule.

with latest_responses as (

    select *
    from {{ source('raw', 'nhl_stats__game') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

games as (

    select
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as game
    from latest_responses

),

renamed as (

    select
        (game ->> 'id')::bigint as game_id,
        (game ->> 'season')::integer as season,
        (game ->> 'gameType')::integer as game_type,
        (game ->> 'gameDate')::date as game_date,
        (game ->> 'gameNumber')::integer as game_number,
        (game ->> 'homeTeamId')::integer as home_team_id,
        (game ->> 'homeScore')::integer as home_score,
        (game ->> 'visitingTeamId')::integer as away_team_id,
        (game ->> 'visitingScore')::integer as away_score,
        (game ->> 'period')::integer as last_period_number,
        (game ->> 'gameStateId')::integer as game_state_id,
        (game ->> 'gameScheduleStateId')::integer as game_schedule_state_id,
        loaded_at
    from games

)

select
    game_id,
    season,
    game_type,
    {{ game_type_label('season', 'game_type') }} as game_type_label,
    game_date,
    game_number,
    home_team_id,
    home_score,
    away_team_id,
    away_score,
    last_period_number,
    game_state_id,
    game_schedule_state_id,
    -- Observed in the 20252026 data: 6 and 7 are finished games, 1 is a game that was never played.
    game_state_id in (6, 7) as is_final,
    loaded_at
from renamed
qualify row_number() over (partition by game_id order by loaded_at desc) = 1
