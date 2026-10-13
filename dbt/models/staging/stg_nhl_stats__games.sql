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
    renamed.game_number,
    renamed.home_team_id,
    renamed.home_score,
    renamed.away_team_id,
    renamed.away_score,
    renamed.last_period_number,
    renamed.game_state_id,
    renamed.game_schedule_state_id,
    -- Observed: finished games have state 6 or 7 and a last period. State 1 is a game not
    -- played. The 20042005 rows have state 6 but no period and a 0-0 score, so the period
    -- is required too.
    renamed.game_state_id in (6, 7) and renamed.last_period_number is not null as is_final,
    renamed.loaded_at
from renamed
left join {{ ref('game_type_labels') }} as season_labels
    on season_labels.season = renamed.season
    and season_labels.game_type = renamed.game_type
left join {{ ref('game_type_labels') }} as all_season_labels
    on all_season_labels.season is null
    and all_season_labels.game_type = renamed.game_type
