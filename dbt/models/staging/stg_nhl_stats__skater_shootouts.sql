-- One row per skater per regular season (skaters with no attempt included), from the NHL stats API's skater shootout report
-- (2005-06 onward; shootouts are regular season only).

with latest_responses as (

    select *
    from {{ source('raw', 'nhl_stats__skater_shootout') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

rows as (

    select
        season,
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as shootout
    from latest_responses

),

renamed as (

    select
        (shootout ->> 'playerId')::bigint as player_id,
        season,
        shootout ->> 'skaterFullName' as skater_name,
        shootout ->> 'teamAbbrevs' as team_abbrevs,
        (shootout ->> 'shootoutGamesPlayed')::integer as shootout_games,
        (shootout ->> 'shootoutShots')::integer as shootout_attempts,
        (shootout ->> 'shootoutGoals')::integer as shootout_goals,
        (shootout ->> 'shootoutGameDecidingGoals')::integer as shootout_deciding_goals,
        loaded_at
    from rows

)

select
    season::varchar || '-' || player_id::varchar as skater_shootout_key,
    *
from renamed
