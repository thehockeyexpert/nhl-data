-- One row per player shift, regular season and playoffs, from 2010-11 (the NHL has no shift charts earlier), linked
-- to fct_games. Times are seconds within the period; game_start_seconds and game_end_seconds count from the opening
-- face-off, with 20-minute periods before overtime. Goal markers in the charts (type 505) are left out.
-- Source: the shift chart (stats API). For a game whose chart is empty, the NHL's HTML shift reports instead (the
-- fallback rule, decided 2026-11-13); their names are matched to the players who played for that team in that game,
-- by full name, else by a last name no teammate in that game shares. Teammates with the same full name (Vancouver's
-- two Elias Petterssons) are told apart by ice time: the one whose official time on ice in that game equals the
-- report's total (report totals matched the official figures to the second in all 1,775 player-games checked).
-- An unmatched name keeps an empty player_id and fails the check shift_players_resolve. When the NHL fills a chart later, the chart replaces the report rows.

-- full_refresh=false (option A, docs/decisions.md): raw keeps only the season in progress, so a full rebuild would
-- lose every older season. `--full-refresh` leaves this table as it is; to rebuild a season, use
-- `uv run python -m ingest.shifts --season <season> --restore` and a normal build.
{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert', full_refresh=false,
          tags=['shifts']) }}

with chart_shifts as (

    select * from {{ ref('stg_nhl_stats__shifts') }}
    where type_code = 517

),

report_shifts as (

    -- Only games with no chart shifts at all.
    select * from {{ ref('stg_nhl_html__shift_reports') }}
    where game_id not in (select game_id from chart_shifts)

),

games as (

    select * from {{ ref('fct_games') }}

),

-- Games with anything new since the last build.
changed_games as (

    select game_id from chart_shifts
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
    union
    select game_id from report_shifts
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

),

-- Who played for each team in the report games, with names as the reports write them (capitals, no accents).
roster as (

    select distinct
        appearances.game_id,
        appearances.team_id,
        appearances.player_id,
        appearances.time_on_ice_seconds,
        upper(strip_accents(players.last_name)) as last_name,
        regexp_replace(upper(strip_accents(players.last_name || ', ' || players.first_name)), '[^A-Z,]', '', 'g') as name_key
    from (
        select game_id, team_id, player_id, time_on_ice_seconds from {{ ref('fct_skater_games') }}
        union all
        select game_id, team_id, player_id, time_on_ice_seconds from {{ ref('fct_goalie_games') }}
    ) as appearances
    inner join {{ ref('dim_players') }} as players on players.player_id = appearances.player_id
    where appearances.game_id in (select game_id from report_shifts)

),

report_players as (

    select
        report_shifts.game_id,
        report_shifts.side,
        report_shifts.sweater_number,
        report_shifts.player_name,
        any_value(case when report_shifts.side = 'home' then games.home_team_id else games.away_team_id end) as team_id,
        -- As the roster writes names: capitals, no accents, letters and the comma only.
        regexp_replace(upper(strip_accents(report_shifts.player_name)), '[^A-Z,]', '', 'g') as name_key,
        upper(strip_accents(split_part(report_shifts.player_name, ',', 1))) as last_name,
        sum(report_shifts.duration_seconds) as report_seconds
    from report_shifts
    inner join games on games.game_id = report_shifts.game_id
    group by report_shifts.game_id, report_shifts.side, report_shifts.sweater_number, report_shifts.player_name

),

matched as (

    select
        report_players.*,
        coalesce(
            -- Full name.
            (select any_value(roster.player_id) from roster
             where roster.game_id = report_players.game_id and roster.team_id = report_players.team_id
               and roster.name_key = report_players.name_key
             having count(*) = 1),
            -- Teammates with the same full name: the one whose official ice time equals the report's total.
            (select any_value(roster.player_id) from roster
             where roster.game_id = report_players.game_id and roster.team_id = report_players.team_id
               and roster.name_key = report_players.name_key
               and roster.time_on_ice_seconds = report_players.report_seconds
             having count(*) = 1),
            -- Else a last name no teammate in that game shares.
            (select any_value(roster.player_id) from roster
             where roster.game_id = report_players.game_id and roster.team_id = report_players.team_id
               and roster.last_name = report_players.last_name
             having count(*) = 1)
        ) as player_id
    from report_players

),

all_shifts as (

    select
        'chart-' || shift_id as shift_key,
        shift_id,
        'shift_chart' as source,
        game_id,
        season,
        game_type,
        player_id,
        team_id,
        null::varchar as report_player_name,
        period_number,
        shift_number,
        start_seconds,
        end_seconds,
        -- The end minus the start, should the NHL's duration be empty (none were when loaded).
        coalesce(duration_seconds, end_seconds - start_seconds) as duration_seconds,
        loaded_at
    from chart_shifts

    union all

    select
        'report-' || report_shifts.report_shift_key as shift_key,
        null::bigint as shift_id,
        'html_report' as source,
        report_shifts.game_id,
        report_shifts.season,
        report_shifts.game_type,
        matched.player_id,
        matched.team_id,
        report_shifts.player_name as report_player_name,
        report_shifts.period_number,
        report_shifts.shift_number,
        report_shifts.start_seconds,
        report_shifts.end_seconds,
        report_shifts.duration_seconds,
        report_shifts.loaded_at
    from report_shifts
    inner join matched
        on matched.game_id = report_shifts.game_id
        and matched.side = report_shifts.side
        and matched.sweater_number = report_shifts.sweater_number

)

select
    all_shifts.shift_key,
    all_shifts.shift_id,
    all_shifts.source,
    all_shifts.game_id,
    all_shifts.season,
    all_shifts.game_type,
    games.game_date,
    all_shifts.player_id,
    all_shifts.report_player_name,
    all_shifts.team_id,
    all_shifts.team_id = games.home_team_id as is_home,
    all_shifts.period_number,
    all_shifts.shift_number,
    all_shifts.start_seconds,
    all_shifts.end_seconds,
    all_shifts.duration_seconds,
    (all_shifts.period_number - 1) * 1200 + all_shifts.start_seconds as game_start_seconds,
    (all_shifts.period_number - 1) * 1200 + all_shifts.end_seconds as game_end_seconds,
    all_shifts.loaded_at
from all_shifts
inner join games on games.game_id = all_shifts.game_id
where all_shifts.game_id in (select game_id from changed_games)
