-- One row per skater per season and game type (regular season, playoffs), from the NHL stats API's skater summary.
-- A player who played for several teams in a season has one row; team_abbrevs lists them (for example "TOR,BOS").

with latest_responses as (

    select *
    from {{ source('raw', 'nhl_stats__skater_season') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

rows as (

    select
        season,
        -- The game type is only in the request: ...and gameTypeId=2
        regexp_extract(source_url, 'gameTypeId=([0-9]+)', 1)::integer as game_type,
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as skater_season
    from latest_responses

),

renamed as (

    select
        (skater_season ->> 'playerId')::bigint as player_id,
        season,
        game_type,
        skater_season ->> 'skaterFullName' as skater_name,
        skater_season ->> 'positionCode' as position_code,
        skater_season ->> 'shootsCatches' as shoots_catches,
        skater_season ->> 'teamAbbrevs' as team_abbrevs,
        (skater_season ->> 'gamesPlayed')::integer as games_played,
        (skater_season ->> 'goals')::integer as goals,
        (skater_season ->> 'assists')::integer as assists,
        (skater_season ->> 'points')::integer as points,
        (skater_season ->> 'plusMinus')::integer as plus_minus,
        (skater_season ->> 'penaltyMinutes')::integer as penalty_minutes,
        (skater_season ->> 'evGoals')::integer as even_strength_goals,
        (skater_season ->> 'evPoints')::integer as even_strength_points,
        (skater_season ->> 'ppGoals')::integer as power_play_goals,
        (skater_season ->> 'ppPoints')::integer as power_play_points,
        (skater_season ->> 'shGoals')::integer as short_handed_goals,
        (skater_season ->> 'shPoints')::integer as short_handed_points,
        (skater_season ->> 'gameWinningGoals')::integer as game_winning_goals,
        (skater_season ->> 'otGoals')::integer as overtime_goals,
        (skater_season ->> 'shots')::integer as shots,
        (skater_season ->> 'timeOnIcePerGame')::double as time_on_ice_per_game_seconds,
        (skater_season ->> 'faceoffWinPct')::double as faceoff_win_pct,
        loaded_at
    from rows

)

select
    season || '-' || game_type || '-' || player_id as skater_season_key,
    *
from renamed
qualify row_number() over (partition by season, game_type, player_id order by loaded_at desc) = 1
