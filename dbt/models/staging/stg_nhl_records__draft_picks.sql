-- One row per draft pick from the NHL records site.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__draft') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

picks as (

    select unnest(json_extract(payload, '$.data[*]')) as pick
    from latest_response

)

select
    (pick ->> 'id')::bigint as draft_pick_id,
    (pick ->> 'draftYear')::integer as draft_year,
    (pick ->> 'roundNumber')::integer as round_number,
    (pick ->> 'pickInRound')::integer as pick_in_round,
    (pick ->> 'overallPickNumber')::integer as overall_pick,
    (pick ->> 'supplementalDraft')::boolean as is_supplemental_draft,
    -- Empty for picks who never received an NHL player ID.
    (pick ->> 'playerId')::bigint as player_id,
    pick ->> 'playerName' as player_name,
    (pick ->> 'draftedByTeamId')::integer as drafted_by_team_id,
    pick ->> 'triCode' as drafted_by_team_abbrev,
    pick ->> 'amateurClubName' as amateur_club,
    pick ->> 'amateurLeague' as amateur_league,
    pick ->> 'position' as position
from picks
