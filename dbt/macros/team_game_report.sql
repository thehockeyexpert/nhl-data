{#
  Unpacks one of the stats API's per-game team reports (isGame=true): one row per team per game, the newest load of
  each winning. Incremental: each build reads only raw responses loaded since the last build, and a row seen again
  (the nightly re-fetch of recent dates, a corrected response) replaces the earlier one for the same game and team.
  columns: a list of [json key, column name, type] for the report's own fields.
#}
{% macro team_game_report(source_table, columns) %}

with new_responses as (

    select *
    from {{ source('raw', source_table) }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}

),

rows as (

    select
        season,
        loaded_at,
        unnest(json_extract(payload, '$.data[*]')) as team_game
    from new_responses

),

renamed as (

    select
        (team_game ->> 'gameId')::bigint as game_id,
        (team_game ->> 'teamId')::integer as team_id,
        season,
        -- The game type is the 5th and 6th digit of the game ID (2025020001 is type 02).
        ((team_game ->> 'gameId')::bigint // 10000 % 100)::integer as game_type,
        (team_game ->> 'gameDate')::date as game_date,
        team_game ->> 'homeRoad' as home_road,
        team_game ->> 'opponentTeamAbbrev' as opponent_abbrev,
        {% for key, name, type in columns %}
        (team_game ->> '{{ key }}')::{{ type }} as {{ name }},
        {% endfor %}
        loaded_at
    from rows

)

select
    game_id || '-' || team_id as team_game_key,
    *
from renamed
qualify row_number() over (partition by game_id, team_id order by loaded_at desc) = 1

{% endmacro %}
