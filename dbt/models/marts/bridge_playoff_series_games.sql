-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- Which playoff series each playoff game belongs to, from the NHL records site's series list.
-- Joins to fct_games on game_id and to fct_playoff_series on playoff_series_key.
-- Only NHL playoff games (game type 3, the 5th and 6th digits of the game ID). The list also holds the 2004 World Cup
-- of Hockey knockout games (game type 7), whose series letters overlap the 2003-04 NHL first round.

select
    season || '-' || playoff_round || '-' || series_letter as playoff_series_key,
    game_id,
    season,
    playoff_round,
    series_letter,
    game_number
from {{ ref('stg_nhl_records__playoff_series_games') }}
where game_id // 10000 % 100 = 3
