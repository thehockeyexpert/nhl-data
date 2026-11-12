-- One row per season-total entry of a player page: a season, league, team and game type, in any league the NHL lists
-- (junior, college, minor and major pro, international tournaments, NHL). Decided 2026-11-11 (docs/decisions.md).
-- Only the newest version of each player's page is kept: a page fetched again with --refresh replaces the old one.
-- A few players have two entries with the same season, league, game type and sequence that differ in team or stats
-- (docs/data_coverage.md, "Player pages"), so the key is the player plus a hash of the whole entry.

with newest_page as (

    select *
    from {{ source('raw', 'nhl_web__player_season_total') }}
    qualify loaded_at = max(loaded_at) over (partition by player_id)

),

renamed as (

    select
        player_id,
        (entry ->> 'season')::integer as season,
        (entry ->> 'gameTypeId')::integer as game_type,
        entry ->> 'leagueAbbrev' as league_abbrev,
        (entry ->> 'sequence')::integer as sequence,
        entry -> 'teamName' ->> 'default' as team_name,
        entry -> 'teamCommonName' ->> 'default' as team_common_name,
        entry -> 'teamPlaceNameWithPreposition' ->> 'default' as team_place_name_with_preposition,
        -- skaters and goalies
        (entry ->> 'gamesPlayed')::integer as games_played,
        (entry ->> 'goals')::integer as goals,
        (entry ->> 'assists')::integer as assists,
        (entry ->> 'points')::integer as points,
        (entry ->> 'pim')::integer as penalty_minutes,
        -- skaters
        (entry ->> 'plusMinus')::integer as plus_minus,
        (entry ->> 'powerPlayGoals')::integer as power_play_goals,
        (entry ->> 'powerPlayPoints')::integer as power_play_points,
        (entry ->> 'shorthandedGoals')::integer as shorthanded_goals,
        (entry ->> 'shorthandedPoints')::integer as shorthanded_points,
        (entry ->> 'gameWinningGoals')::integer as game_winning_goals,
        (entry ->> 'otGoals')::integer as ot_goals,
        (entry ->> 'shots')::integer as shots,
        (entry ->> 'shootingPctg')::double as shooting_pct,
        (entry ->> 'faceoffWinningPctg')::double as faceoff_win_pct,
        split_part(entry ->> 'avgToi', ':', 1)::integer * 60
            + split_part(entry ->> 'avgToi', ':', 2)::integer as avg_toi_seconds,
        -- goalies
        (entry ->> 'gamesStarted')::integer as games_started,
        (entry ->> 'wins')::integer as wins,
        (entry ->> 'losses')::integer as losses,
        (entry ->> 'ties')::integer as ties,
        (entry ->> 'otLosses')::integer as ot_losses,
        (entry ->> 'shutouts')::integer as shutouts,
        (entry ->> 'goalsAgainst')::integer as goals_against,
        (entry ->> 'shotsAgainst')::integer as shots_against,
        (entry ->> 'goalsAgainstAvg')::double as goals_against_avg,
        (entry ->> 'savePctg')::double as save_pct,
        split_part(entry ->> 'timeOnIce', ':', 1)::integer * 60
            + split_part(entry ->> 'timeOnIce', ':', 2)::integer as time_on_ice_seconds,
        md5(entry::varchar) as entry_hash,
        payload_hash,
        source_url,
        loaded_at
    from newest_page

)

select
    player_id || '-' || entry_hash as season_total_key,
    *
from renamed
-- An entry repeated word for word on the same page is one entry.
qualify row_number() over (partition by player_id, entry_hash order by loaded_at) = 1
