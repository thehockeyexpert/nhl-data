{#
    The failing rows of one data check, minus the documented exceptions in
    seeds/check_exceptions.csv. A test built on this passes when no rows come back.

    An exception matches on check name and season. If it names a game it covers only
    that game; if not, it covers that check for the whole season.
#}
{% macro unexcepted_failures(check_name) -%}
    select failures.*
    from {{ ref('check_failures') }} as failures
    where failures.check_name = '{{ check_name }}'
      and not exists (
          select 1
          from {{ ref('check_exceptions') }} as exceptions
          where exceptions.check_name = failures.check_name
            and exceptions.season = failures.season
            and (exceptions.game_id is null or exceptions.game_id = failures.game_id)
      )
{%- endmacro %}
