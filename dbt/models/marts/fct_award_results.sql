-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- One row per award result: a winner, runner-up or finalist for a trophy in a season, from the NHL records site.
-- A result names a player, a coach, a general manager or only a team, depending on the trophy.
-- Several winners in one season are normal for some trophies: the Stanley Cup lists every player engraved on it,
-- and the Vezina, Jennings and Rocket Richard trophies have been shared.

with results as (

    select * from {{ ref('stg_nhl_records__award_results') }}

),

trophies as (

    select trophy_id, trophy_name from {{ ref('dim_trophies') }}

)

select
    results.award_result_id,
    results.trophy_id,
    trophies.trophy_name,
    results.season,
    results.status,
    results.status = 'WINNER' as is_winner,
    results.player_id,
    results.coach_id,
    results.general_manager_id,
    results.team_id,
    results.full_name,
    results.is_rookie
from results
left join trophies on trophies.trophy_id = results.trophy_id
