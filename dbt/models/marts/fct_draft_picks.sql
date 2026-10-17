-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- One row per NHL draft pick, 1963 onward, from the NHL records site.
-- player_id is empty for the picks who never received an NHL player ID; most of those never played in the NHL.
-- season is the season that ends in the draft's year (the 2015 draft is 20142015), so a draft joins to dim_seasons.

with picks as (

    select * from {{ ref('stg_nhl_records__draft_picks') }}

),

players as (

    select player_id, is_nhl_player from {{ ref('dim_players') }}

)

select
    picks.draft_pick_id,
    picks.draft_year,
    (picks.draft_year - 1) * 10000 + picks.draft_year as season,
    picks.round_number,
    picks.pick_in_round,
    picks.overall_pick,
    picks.player_id,
    picks.player_name,
    coalesce(players.is_nhl_player, false) as is_nhl_player,
    picks.drafted_by_team_id as team_id,
    picks.drafted_by_team_abbrev as team_abbrev,
    picks.position,
    picks.amateur_club,
    picks.amateur_league
from picks
left join players on players.player_id = picks.player_id
