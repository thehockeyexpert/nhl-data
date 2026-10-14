{% macro unexcepted_failures(check_name) -%}
    select failures.*
    from {{ ref('check_failures') }} as failures
    where failures.check_name = '{{ check_name }}'
      and not exists (
          select 1 from {{ ref('check_exceptions') }} as exceptions
          where exceptions.check_name = failures.check_name
            and exceptions.season = failures.season
            and (exceptions.game_id is null or exceptions.game_id = failures.game_id)
            and (exceptions.team_id is null or exceptions.team_id = failures.team_id))
{%- endmacro %}
