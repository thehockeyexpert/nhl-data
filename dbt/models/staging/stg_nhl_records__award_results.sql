-- One row per award result (winner, runner-up or finalist) from the NHL records site.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__award_details') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

results as (

    select unnest(json_extract(payload, '$.data[*]')) as result
    from latest_response

)

select
    (result ->> 'id')::bigint as award_result_id,
    (result ->> 'trophyId')::integer as trophy_id,
    (result ->> 'seasonId')::integer as season,
    result ->> 'status' as status,
    -- A result names a player, a coach, a general manager or only a team, depending on the trophy.
    -- Observed: the NHL uses player ID 0 on results for people who are not in its player list
    -- (community and Lester Patrick awards), so 0 is stored as empty, not as a player.
    nullif((result ->> 'playerId')::bigint, 0) as player_id,
    (result ->> 'coachId')::bigint as coach_id,
    (result ->> 'generalManagerId')::bigint as general_manager_id,
    (result ->> 'teamId')::integer as team_id,
    result ->> 'fullName' as full_name,
    (result ->> 'isRookie')::boolean as is_rookie
from results
