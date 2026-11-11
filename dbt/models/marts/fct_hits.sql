-- One row per hit from the play-by-play, regular season and playoffs, from 2007-08, linked to fct_games.
-- The hitting team is the event's owner team (checked against the rosters: docs/data_coverage.md, "Hits and penalties").

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', tags=['play_by_play']) }}

with hits as (

    select * from {{ ref('stg_nhl_web__pbp_events') }}
    where event_type = 'hit'
    {% if is_incremental() %}
        and loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

)

select
    hits.event_key as hit_key,
    hits.game_id,
    hits.season,
    hits.game_type,
    games.game_date,
    hits.event_id,
    hits.period_number,
    hits.period_type,
    hits.time_in_period_seconds,
    hits.situation_code,
    hits.event_owner_team_id as hitting_team_id,
    case when hits.event_owner_team_id = games.home_team_id then games.away_team_id else games.home_team_id end
        as hit_team_id,
    hits.hitting_player_id,
    hits.hittee_player_id,
    hits.x_coord,
    hits.y_coord,
    hits.zone_code,
    hits.loaded_at
from hits
left join {{ ref('fct_games') }} as games on games.game_id = hits.game_id
