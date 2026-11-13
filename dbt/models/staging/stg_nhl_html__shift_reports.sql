-- One row per shift in the NHL's HTML shift reports (home TH, visitor TV), stored only for games whose shift chart
-- came back empty (the fallback rule, decided 2026-11-13). Parsed from the HTML exactly as received: a heading per
-- player ("6 LOHREI, MASON"), then one table row per shift (number, period, start and end as elapsed / remaining,
-- duration). The reports carry sweater numbers and names, not player IDs: fct_shifts matches the names.
-- The newest copy of each report wins.

{{ config(materialized='table', tags=['shifts']) }}

with reports as (

    select *
    from {{ source('raw', 'nhl_html__shift_report') }}
    qualify loaded_at = max(loaded_at) over (partition by source_url)

),

sections as (

    select
        game_id,
        season,
        source_url,
        loaded_at,
        case regexp_extract(source_url, '/(T[HV])\d+\.HTM$', 1) when 'TH' then 'home' when 'TV' then 'away' end as side,
        unnest(string_split(body, 'class="playerHeading + border" colspan="8">')[2:]) as section
    from reports

),

players as (

    select
        *,
        regexp_extract(section, '^(\d+) ([^<]*)</td>', ['sweater_number', 'player_name']) as player
    from sections

),

shift_rows as (

    select
        game_id,
        season,
        source_url,
        loaded_at,
        side,
        player.sweater_number::integer as sweater_number,
        trim(player.player_name) as player_name,
        unnest(regexp_extract_all(
            section,
            '<td align="center" class="lborder \+ bborder">\d+</td>\s*'
            || '<td align="center" class="lborder \+ bborder">\w+</td>\s*'
            || '<td align="center" class="lborder \+ bborder">[\d:]+ / [\d:]+</td>\s*'
            || '<td align="center" class="lborder \+ bborder">[\d:]+ / [\d:]+</td>\s*'
            || '<td align="center" class="lborder \+ bborder">[\d:]+</td>'
        )) as shift_row
    from players

),

parsed as (

    select
        *,
        regexp_extract(
            shift_row,
            '>(\d+)</td>\s*<td[^>]*>(\w+)</td>\s*<td[^>]*>([\d:]+) / [\d:]+</td>\s*<td[^>]*>([\d:]+) / [\d:]+</td>\s*<td[^>]*>([\d:]+)</td>',
            ['shift_number', 'period', 'start_time', 'end_time', 'duration']
        ) as shift
    from shift_rows

)

select
    game_id || '-' || side || '-' || sweater_number || '-' || shift.shift_number as report_shift_key,
    game_id,
    season,
    (game_id // 10000 % 100)::integer as game_type,
    side,
    sweater_number,
    player_name,
    shift.shift_number::integer as shift_number,
    -- 'OT' is the overtime period, the 4th.
    case when shift.period = 'OT' then 4 else try_cast(shift.period as integer) end as period_number,
    split_part(shift.start_time, ':', 1)::integer * 60 + split_part(shift.start_time, ':', 2)::integer as start_seconds,
    split_part(shift.end_time, ':', 1)::integer * 60 + split_part(shift.end_time, ':', 2)::integer as end_seconds,
    split_part(shift.duration, ':', 1)::integer * 60 + split_part(shift.duration, ':', 2)::integer as duration_seconds,
    source_url,
    loaded_at
from parsed
